import asyncio
import logging
import enum
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .schemas import SceneDef, TimingManifest, GeneratedScene, SceneAudioManifest
from .config import get_settings

settings = get_settings()
logger = logging.getLogger("phase3.animator")

class AnimationError(Exception):
    pass

class AudioSyncError(Exception):
    pass

class KenBurnsEffect(str, enum.Enum):
    ZOOM_IN = "ZOOM_IN"
    ZOOM_OUT = "ZOOM_OUT"
    PAN_LEFT = "PAN_LEFT"
    PAN_RIGHT = "PAN_RIGHT"
    PAN_UP = "PAN_UP"
    PAN_DOWN = "PAN_DOWN"

    @classmethod
    def from_mood(cls, mood: str) -> "KenBurnsEffect":
        mood_map = {
            "happy":       cls.ZOOM_IN,
            "sad":         cls.PAN_DOWN,
            "dark":        cls.ZOOM_OUT,
            "epic":        cls.PAN_LEFT,
            "mysterious":  cls.PAN_RIGHT,
            "angry":       cls.ZOOM_OUT,
            "romantic":    cls.ZOOM_IN,
            "neutral":     cls.ZOOM_IN,
        }
        return mood_map.get(mood.lower(), cls.ZOOM_IN)

async def _run_ffmpeg(args: List[str], error_class=Exception) -> None:
    """Run FFmpeg in a worker thread to avoid Windows event-loop subprocess limitations."""
    cmd = [str(settings.FFMPEG_PATH), *map(str, args)]
    logger.debug(f"Running FFmpeg: {' '.join(cmd)}")

    def _exec() -> subprocess.CompletedProcess:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    proc = await asyncio.to_thread(_exec)

    if proc.returncode != 0:
        error_msg = proc.stderr.decode(errors="replace").strip()
        logger.error(f"FFmpeg error: {error_msg}")
        raise error_class(f"FFmpeg failed: {error_msg}")

def build_kenburns_filter(effect: KenBurnsEffect, duration_seconds: float, width: int, height: int) -> str:
    """Build FFmpeg zoompan filter string for Ken Burns effect."""
    total_frames = int(duration_seconds * 25)
    
    if effect == KenBurnsEffect.ZOOM_IN:
        filter_str = f"zoompan=z='min(zoom+0.001,1.3)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}"
    elif effect == KenBurnsEffect.ZOOM_OUT:
        filter_str = f"zoompan=z='if(lte(zoom,1.0),1.3,max(1.0,zoom-0.001))':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}"
    elif effect == KenBurnsEffect.PAN_LEFT:
        filter_str = f"zoompan=z=1.2:d={total_frames}:x='min(iw*(zoom-1)/2+on*0.32,iw*(zoom-1))':y='ih/2-(ih/zoom/2)':s={width}x{height}"
    elif effect == KenBurnsEffect.PAN_RIGHT:
        filter_str = f"zoompan=z=1.2:d={total_frames}:x='max(iw*(zoom-1)/2-on*0.32,0)':y='ih/2-(ih/zoom/2)':s={width}x{height}"
    elif effect == KenBurnsEffect.PAN_UP:
        filter_str = f"zoompan=z=1.2:d={total_frames}:x='iw/2-(iw/zoom/2)':y='min(ih*(zoom-1)/2+on*0.32,ih*(zoom-1))':s={width}x{height}"
    elif effect == KenBurnsEffect.PAN_DOWN:
        filter_str = f"zoompan=z=1.2:d={total_frames}:x='iw/2-(iw/zoom/2)':y='max(ih*(zoom-1)/2-on*0.32,0)':s={width}x{height}"
    else:
        filter_str = f"zoompan=z=1.1:d={total_frames}:s={width}x{height}"
        
    return f"{filter_str},format=yuv420p"

async def animate_scene_clip(image_path: Path, scene: SceneDef, output_dir: Path) -> Path:
    """Create animated MP4 from static image with Ken Burns effect."""
    effect = KenBurnsEffect.from_mood(scene.mood)
    filter_string = build_kenburns_filter(effect, scene.duration_seconds, settings.IMAGE_WIDTH, settings.IMAGE_HEIGHT)
    output_path = output_dir / f"{scene.scene_id}_animated.mp4"
    
    args = [
        "-loop", "1", "-i", str(image_path),
        "-vf", filter_string,
        "-t", str(scene.duration_seconds),
        "-r", str(settings.VIDEO_FPS),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(output_path), "-y"
    ]
    
    await _run_ffmpeg(args, AnimationError)
    logger.info(f"[Animator] Scene {scene.scene_id} animated with {effect.value}")
    return output_path

async def animate_all_scenes(scene_image_map: Dict[str, Path], scenes: List[SceneDef], output_dir: Path) -> Dict[str, Path]:
    """Animate all scene images concurrently."""
    tasks = []
    scene_lookup = {s.scene_id: s for s in scenes}
    scene_ids = list(scene_image_map.keys())
    for sid in scene_ids:
        image_path = scene_image_map[sid]
        scene = scene_lookup.get(sid)
        if scene:
            tasks.append(animate_scene_clip(image_path, scene, output_dir))
            
    results = await asyncio.gather(*tasks)
    return {sid: path for sid, path in zip(scene_ids, results)}

async def merge_audio_video(clip_path: Path, scene_manifest: SceneAudioManifest, output_dir: Path) -> Path:
    """Merge animated clip with scene audio (Dialogue + BGM)."""
    output_path = output_dir / f"{scene_manifest.scene_id}_synced.mp4"
    
    # If per-scene BGM is present, mix it in
    if scene_manifest.bgm_file and Path(scene_manifest.bgm_file).exists():
        args = [
            "-i", str(clip_path),
            "-i", str(scene_manifest.audio_file),
            "-i", str(scene_manifest.bgm_file),
            "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            str(output_path), "-y"
        ]
    else:
        args = [
            "-i", str(clip_path),
            "-i", str(scene_manifest.audio_file),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path), "-y"
        ]
    
    await _run_ffmpeg(args, AudioSyncError)
    logger.info(f"[Animator] Audio synced for scene {scene_manifest.scene_id} (BGM: {bool(scene_manifest.bgm_file)})")
    return output_path

async def sync_all_scenes(animated_clips: Dict[str, Path], scene_image_map: Dict[str, Path], timing_manifest: TimingManifest, scenes: List[SceneDef], output_dir: Path) -> List[GeneratedScene]:
    """Sync audio for all clips sequentially and update duration."""
    sorted_scenes = sorted(scenes, key=lambda s: s.sequence)
    results = []
    
    for scene in sorted_scenes:
        scene_manifest = timing_manifest.get_scene(scene.scene_id)
        if not scene_manifest:
            logger.warning(f"[Animator] No timing manifest for scene {scene.scene_id}, skipping")
            continue
            
        clip_path = animated_clips.get(scene.scene_id)
        if not clip_path: continue
            
        synced_path = await merge_audio_video(clip_path, scene_manifest, output_dir)
        
        actual_duration = scene_manifest.end_ms / 1000.0
        
        generated = GeneratedScene(
            scene_id=scene.scene_id,
            sequence=scene.sequence,
            image_path=scene_image_map[scene.scene_id],
            clip_path=synced_path,
            duration_seconds=actual_duration,
            audio_path=Path(scene_manifest.audio_file),
            bgm_path=Path(scene_manifest.bgm_file) if scene_manifest.bgm_file else None
        )
        results.append(generated)
        
    return results
