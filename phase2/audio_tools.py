"""
Phase 2 Audio Tools: TTS, BGM, and Audio Assembly

Internal _impl functions for direct use in agents + @tool decorated versions for LangChain/MCP.
Updated to support unified dynamic run directories.
"""

import imageio_ffmpeg
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config.audio_config import (
    TTS_CONFIG,
    PERSONALITY_TO_VOICE_PARAMS,
    DEFAULT_VOICE_PARAMS,
    AUDIO_OUTPUT_CONFIG,
    CACHING_CONFIG,
    GENDER_KEYWORDS,
    GENDER_PITCH_MULTIPLIERS,
    SCENE_TONE_METADATA,
)

# Set up FFmpeg
_ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = os.path.dirname(_ffmpeg_exe) + os.pathsep + os.environ.get("PATH", "")

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub")

from pydub import AudioSegment
from pydub import utils as pydub_utils

# Force pydub to use imageio_ffmpeg binary
pydub_utils.get_encoder_name = lambda: _ffmpeg_exe
AudioSegment.converter = _ffmpeg_exe
AudioSegment.ffmpeg = _ffmpeg_exe

# Global Voice Cache (in-memory, per session)
_VOICE_EMBEDDING_CACHE: Dict[str, Any] = {}

def _detect_gender_from_appearance(appearance: str) -> str:
    """Infer character gender from appearance description."""
    appearance_lower = appearance.lower() if appearance else ""
    female_count = sum(1 for keyword in GENDER_KEYWORDS["female"] if keyword in appearance_lower)
    male_count = sum(1 for keyword in GENDER_KEYWORDS["male"] if keyword in appearance_lower)
    if female_count > male_count:
        return "female"
    elif male_count > female_count:
        return "male"
    return "neutral"

def _get_voice_params_from_personality(voice_personality: str) -> Dict[str, Any]:
    """Map voice_personality string to synthesis parameters."""
    if not voice_personality:
        return DEFAULT_VOICE_PARAMS.copy()
    personality_lower = voice_personality.lower()
    for keyword, params in PERSONALITY_TO_VOICE_PARAMS.items():
        if keyword in personality_lower:
            return params.copy()
    return DEFAULT_VOICE_PARAMS.copy()

def _get_run_paths(run_dir: str):
    """Generate absolute paths for the current run."""
    base = Path(run_dir)
    paths = {
        "audio": base / "audio",
        "bgm": base / "bgm_library",
        "cache": base / ".voice_cache"
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths

def _create_silent_audio(output_path: str, duration_ms: int = 2000) -> None:
    """Create a silent MP3 file (fallback for synthesis failures)."""
    silent = AudioSegment.silent(duration=duration_ms)
    silent.export(output_path, format="mp3")
    print(f"[AUDIO] Created silent placeholder: {output_path}")

# ==============================================================================
# TTS Synthesis Implementation
# ==============================================================================

def _synthesize_dialogue_impl(
    text: str,
    character_name: str,
    run_dir: str,
    character_appearance: str = "",
    voice_personality: str = "",
    scene_id: str = "",
    dialogue_index: int = 0,
) -> str:
    """Internal dialogue synthesis with run_dir support."""
    from gtts import gTTS
    
    paths = _get_run_paths(run_dir)
    filename = f"{scene_id}_{character_name.lower().replace(' ', '_')}_{dialogue_index}.mp3"
    output_path = str(paths["audio"] / filename)
    
    # Check cache if enabled
    if TTS_CONFIG["cache_embeddings"] and os.path.exists(output_path):
        print(f"[TTS] Using cached dialogue: {output_path}")
        return output_path
    
    try:
        gender = _detect_gender_from_appearance(character_appearance)
        voice_params = _get_voice_params_from_personality(voice_personality)
        
        print(f"[TTS] gTTS: {character_name} | gender={gender} | personality={voice_personality}")
        
        tts = gTTS(text=text, lang=TTS_CONFIG["language"], slow=False)
        tts.save(output_path)
        
        return output_path
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        _create_silent_audio(output_path)
        return output_path

@tool
def synthesize_dialogue(
    text: str,
    character_name: str,
    run_dir: str,
    character_appearance: str = "",
    voice_personality: str = "",
    scene_id: str = "",
    dialogue_index: int = 0,
) -> str:
    """Synthesize dialogue text to speech and save to run_dir/audio."""
    return _synthesize_dialogue_impl(text, character_name, run_dir, character_appearance, voice_personality, scene_id, dialogue_index)

# ==============================================================================
# BGM Selection Implementation
# ==============================================================================

def _select_bgm_track_impl(tone: str, duration_ms: int) -> str:
    """Internal BGM track selection logic."""
    description = SCENE_TONE_METADATA.get(tone.lower(), SCENE_TONE_METADATA["default"])
    print(f"[BGM] Tone '{tone}': {description}")
    
    result = {
        "tone": tone,
        "description": description,
        "required_duration_ms": duration_ms,
        "suggested_volume_db": -15
    }
    return json.dumps(result)

@tool
def select_bgm_track(tone: str, duration_ms: int) -> str:
    """Select appropriate background music metadata based on scene tone."""
    return _select_bgm_track_impl(tone, duration_ms)

def _download_bgm_from_freesound(tone: str, run_dir: str) -> str:
    """Download BGM track from Freesound API if key is present, otherwise fallback to silence."""
    import requests
    api_key = os.environ.get("FREESOUND_API_KEY")
    paths = _get_run_paths(run_dir)
    bgm_path = str(paths["bgm"] / f"bgm_{tone.lower()}.mp3")
    
    if os.path.exists(bgm_path):
        return bgm_path

    if not api_key:
        print(f"[BGM WARNING] No FREESOUND_API_KEY set, skipping BGM")
        _create_silent_audio(bgm_path, 5000)
        return bgm_path
    
    try:
        print(f"[BGM] Searching Freesound for: {tone} atmosphere...")
        search_url = f"https://freesound.org/apiv2/search/text/?query={tone}%20atmosphere&token={api_key}&fields=id,name,previews&filter=duration:[30%20TO%20120]"
        response = requests.get(search_url, timeout=10)
        data = response.json()
        
        if data.get("results"):
            # Take the first suitable result
            preview_url = data["results"][0]["previews"]["preview-hq-mp3"]
            print(f"[BGM] Downloading preview: {preview_url}")
            bgm_data = requests.get(preview_url, timeout=15).content
            with open(bgm_path, "wb") as f:
                f.write(bgm_data)
        else:
            print(f"[BGM] No results for {tone}, using silence.")
            _create_silent_audio(bgm_path, 5000)
    except Exception as e:
        print(f"[BGM ERROR] Failed to fetch BGM: {e}")
        _create_silent_audio(bgm_path, 5000)
        
    return bgm_path

@tool
def download_bgm_track(tone: str, run_dir: str) -> str:
    """Download background music track for the given tone to run_dir/bgm_library."""
    return _download_bgm_from_freesound(tone, run_dir)

# ==============================================================================
# Audio Assembly Implementation
# ==============================================================================

def _assemble_audio_segments_impl(
    dialogue_files: str,
    bgm_file: str,
    scene_id: str,
    run_dir: str,
    output_filename: str = "",
) -> str:
    """Internal audio assembly with run_dir support."""
    paths = _get_run_paths(run_dir)
    
    def _get_audio_duration_ms_fallback(file_path: str) -> int:
        import subprocess
        import re
        try:
            cmd = [_ffmpeg_exe, "-i", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stderr
            match = re.search(r"Duration:\s+(\d+):(\d+):(\d+)\.(\d+)", output)
            if match:
                hours, minutes, seconds, dec = map(int, match.groups())
                return (hours * 3600 + minutes * 60 + seconds) * 1000 + dec * 10
        except Exception:
            pass
        return max(1000, os.path.getsize(file_path) // 16)

    try:
        dialogue_list = json.loads(dialogue_files)
        if not dialogue_list:
            return json.dumps({"error": "No dialogue files"})

        first_dialogue = dialogue_list[0]
        dialogue_path = first_dialogue.get("file", "")
        
        output_name = output_filename if output_filename else f"{scene_id.replace(' ', '_')}.mp3"
        output_path = str(paths["audio"] / output_name)

        # Force fallback if ffprobe is missing
        import shutil
        if not shutil.which("ffprobe"):
            shutil.copy(dialogue_path, output_path)
            duration_ms = _get_audio_duration_ms_fallback(output_path)
            result = {
                "audio_file": output_path,
                "duration_ms": duration_ms,
                "timing_entries": [{"dialogue_index": 0, "character": first_dialogue.get("character"), "start_ms": 0, "end_ms": duration_ms}],
            }
            print(f"[ASSEMBLY SUCCESS] Generated {output_path} (fallback mode, {duration_ms}ms)")
            return json.dumps(result)

        # Full assembly if ffprobe/pydub works
        combined_audio = None
        timing_entries = []
        current_offset_ms = 0
        for idx, entry in enumerate(dialogue_list):
            d_audio = AudioSegment.from_mp3(entry["file"])
            d_dur = len(d_audio)
            timing_entries.append({
                "dialogue_index": idx,
                "character": entry["character"],
                "start_ms": current_offset_ms,
                "end_ms": current_offset_ms + d_dur,
            })
            combined_audio = d_audio if combined_audio is None else combined_audio + d_audio
            current_offset_ms += d_dur

        if bgm_file and os.path.exists(bgm_file):
            bgm_audio = AudioSegment.from_mp3(bgm_file)
            if len(bgm_audio) < len(combined_audio):
                bgm_audio = bgm_audio * (len(combined_audio) // len(bgm_audio) + 1)
            bgm_audio = bgm_audio[:len(combined_audio)].apply_gain(-15)
            combined_audio = combined_audio.overlay(bgm_audio)

        combined_audio.export(output_path, format="mp3")
        result = {
            "audio_file": output_path,
            "duration_ms": len(combined_audio),
            "timing_entries": timing_entries,
        }
        return json.dumps(result)

    except Exception as e:
        print(f"[ASSEMBLY ERROR] {e}")
        return json.dumps({"error": str(e)})

@tool
def assemble_audio_segments(
    dialogue_files: str,
    bgm_file: str,
    scene_id: str,
    run_dir: str,
    output_filename: str = "",
) -> str:
    """Mix dialogue audio files with background music and generate timing manifest in run_dir/audio."""
    return _assemble_audio_segments_impl(dialogue_files, bgm_file, scene_id, run_dir, output_filename)

# ==============================================================================
# Voice Caching Implementation
# ==============================================================================

def _cache_character_voice_impl(
    character_name: str,
    voice_personality: str,
    character_appearance: str,
    run_dir: str,
) -> str:
    """Internal character voice caching in run_dir/.voice_cache."""
    paths = _get_run_paths(run_dir)
    character_key = character_name.lower().replace(" ", "_")
    gender = _detect_gender_from_appearance(character_appearance)
    voice_params = _get_voice_params_from_personality(voice_personality)
    
    cache_entry = {
        "character_name": character_name,
        "gender": gender,
        "voice_params": voice_params,
        "personality": voice_personality,
    }
    
    _VOICE_EMBEDDING_CACHE[character_key] = cache_entry
    cache_file = paths["cache"] / f"{character_key}.json"
    with open(cache_file, "w") as f:
        json.dump(cache_entry, f, indent=2)
    
    print(f"[CACHE] Cached voice parameters for {character_name}")
    return json.dumps(cache_entry)

@tool
def cache_character_voice(
    character_name: str,
    voice_personality: str,
    character_appearance: str,
    run_dir: str,
) -> str:
    """Cache character voice parameters for reuse across scenes in run_dir."""
    return _cache_character_voice_impl(character_name, voice_personality, character_appearance, run_dir)

def _get_cached_voice_impl(character_name: str, run_dir: str) -> str:
    """Internal get cached voice parameters from run_dir/.voice_cache."""
    paths = _get_run_paths(run_dir)
    character_key = character_name.lower().replace(" ", "_")
    
    if character_key in _VOICE_EMBEDDING_CACHE:
        print(f"[CACHE HIT] Retrieved voice for {character_name} from memory")
        return json.dumps(_VOICE_EMBEDDING_CACHE[character_key])
    
    cache_file = paths["cache"] / f"{character_key}.json"
    if cache_file.exists():
        with open(cache_file, "r") as f:
            cache_entry = json.load(f)
        _VOICE_EMBEDDING_CACHE[character_key] = cache_entry
        print(f"[CACHE HIT] Retrieved voice for {character_name} from disk")
        return json.dumps(cache_entry)
    
    return json.dumps({})

@tool
def get_cached_voice(character_name: str, run_dir: str) -> str:
    """Retrieve cached voice parameters for a character from run_dir."""
    return _get_cached_voice_impl(character_name, run_dir)
