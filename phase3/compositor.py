import asyncio
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import aiofiles

from .schemas import GeneratedScene, TimingManifest, BackgroundMusic, PipelineInput
from .animator import _run_ffmpeg
from .config import get_settings

settings = get_settings()
logger = logging.getLogger("phase3.compositor")

class CompositionError(Exception):
    pass

def build_concat_filter(scenes: List[GeneratedScene], transition_duration: float = 0.5) -> Tuple[str, str]:
    """Build FFmpeg filter_complex for concatenating scenes with xfade transitions."""
    if len(scenes) == 1:
        return "[0:v]copy[vout]", "vout"
        
    filter_chain = ""
    offset = 0.0
    last_label = "0:v"
    
    for i in range(len(scenes) - 1):
        offset += scenes[i].duration_seconds - transition_duration
        current_label = f"v{i}{i+1}"
        
        input1 = last_label
        input2 = f"{i+1}:v"
        
        filter_chain += f"[{input1}][{input2}]xfade=transition=fade:duration={transition_duration}:offset={offset:.3f}[{current_label}];"
        last_label = current_label
        
    return filter_chain.rstrip(";"), last_label

async def concatenate_scenes(generated_scenes: List[GeneratedScene], output_path: Path, transition_duration: float = 0.5) -> Path:
    """Stitch all scene clips together using FFmpeg concat filter with transitions."""
    sorted_scenes = sorted(generated_scenes, key=lambda s: s.sequence)
    num_scenes = len(sorted_scenes)
    
    args = []
    for scene in sorted_scenes:
        args.extend(["-i", str(scene.clip_path)])
        
    v_filter, v_label = build_concat_filter(sorted_scenes, transition_duration)
    
    # Audio concat filter
    a_inputs = "".join([f"[{i}:a]" for i in range(num_scenes)])
    a_filter = f"{a_inputs}concat=n={num_scenes}:v=0:a=1[aout]"
    
    full_filter = f"{v_filter};{a_filter}" if v_filter else a_filter
    v_map = f"[{v_label}]" if v_label else "[0:v]"
    
    args.extend([
        "-filter_complex", full_filter,
        "-map", v_map,
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac",
        str(output_path), "-y"
    ])
    
    await _run_ffmpeg(args, CompositionError)
    logger.info(f"[Compositor] Concatenated {len(generated_scenes)} scenes")
    return output_path

async def mix_background_music(video_path: Path, bgm: BackgroundMusic, output_path: Path) -> Path:
    """Overlay background music with the video's audio track."""
    if not Path(bgm.audio_file).exists():
        logger.warning(f"[Compositor] BGM file not found: {bgm.audio_file}, skipping music mix")
        return video_path
        
    args = [
        "-i", str(video_path),
        "-i", str(bgm.audio_file),
        "-filter_complex", f"[1:a]volume={bgm.volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac",
        str(output_path), "-y"
    ]
    
    await _run_ffmpeg(args, CompositionError)
    logger.info(f"[Compositor] Background music mixed from {bgm.audio_file}")
    return output_path

def generate_srt_content(generated_scenes: List[GeneratedScene], pipeline_input: PipelineInput, timing_manifest: TimingManifest) -> str:
    """Generate SRT subtitle content from timing manifest and pipeline input."""
    def format_timestamp(ms: int) -> str:
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    srt_entries = []
    index = 1
    global_time_ms = 0
    
    sorted_scenes = sorted(generated_scenes, key=lambda s: s.sequence)
    
    for scene in sorted_scenes:
        scene_manifest = timing_manifest.get_scene(scene.scene_id)
        if not scene_manifest:
            global_time_ms += int(scene.duration_seconds * 1000)
            continue
            
        scene_def = pipeline_input.get_scene(scene.scene_id)
        
        for i, segment in enumerate(scene_manifest.dialogue_segments):
            char_name = segment.character_id # Fallback
            if pipeline_input.characters:
                char = pipeline_input.get_character(segment.character_id)
                if char: char_name = char.name
            
            line_text = "..."
            if scene_def and i < len(scene_def.dialogue):
                line_text = scene_def.dialogue[i].line
            
            start = global_time_ms + segment.start_ms
            end = global_time_ms + segment.end_ms
            
            srt_entries.append(f"{index}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{char_name}: {line_text}\n")
            index += 1
            
        global_time_ms += scene_manifest.end_ms 
        
    return "\n".join(srt_entries)

async def burn_subtitles(video_path: Path, srt_content: str, output_dir: Path) -> Path:
    """Burn subtitles into the video file using FFmpeg subtitles filter."""
    srt_path = output_dir / "subtitles.srt"
    async with aiofiles.open(srt_path, "w") as f:
        await f.write(srt_content)
        
    output_path = output_dir / "final_output_subtitled.mp4"
    style = "FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Bold=1,Outline=2"
    
    # Normalize path for FFmpeg subtitles filter: use forward slashes and escape colons
    safe_srt_path = str(srt_path).replace('\\', '/').replace(":", "\\:").replace("'", "\\'")

    # Build filter without extra surrounding quotes around the path (FFmpeg parses it reliably)
    vf_filter = f"subtitles={safe_srt_path}:force_style='{style}'"
    args = [
        "-i", str(video_path),
        "-vf", vf_filter,
        "-c:a", "copy",
        str(output_path), "-y"
    ]
    
    await _run_ffmpeg(args, CompositionError)
    logger.info(f"[Compositor] Subtitles burned into {output_path}")
    return output_path

async def compose_final_video(generated_scenes: List[GeneratedScene], timing_manifest: TimingManifest, output_dir: Path, add_subtitles: bool = False, pipeline_input: Optional[PipelineInput] = None) -> Path:
    """Complete the final production steps: concatenation, BGM mixing, and subtitling."""
    concat_path = output_dir / "concatenated.mp4"
    await concatenate_scenes(generated_scenes, concat_path)
    
    final_path = output_dir / "final_output.mp4"
    if timing_manifest.background_music:
        await mix_background_music(concat_path, timing_manifest.background_music, final_path)
    else:
        import shutil
        shutil.copy(str(concat_path), str(final_path))
        
    if add_subtitles and pipeline_input:
        srt_content = generate_srt_content(generated_scenes, pipeline_input, timing_manifest)
        if srt_content.strip():
            try:
                final_path = await burn_subtitles(final_path, srt_content, output_dir)
            except Exception as e:
                logger.error(f"[Compositor] Subtitle burn failed: {e}")
            
    return final_path
