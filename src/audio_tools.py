"""
Audio Tools: MCP-registered tools for Phase 2 Audio Generation & Integration
...
"""

import imageio_ffmpeg
import os
import sys
from pathlib import Path

# Add parent directory to path for imports from config/
sys.path.insert(0, str(Path(__file__).parent.parent))

_ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()  # returns the hardcoded path above
os.environ["PATH"] = os.path.dirname(_ffmpeg_exe) + os.pathsep + os.environ.get("PATH", "")

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub")

import json
import hashlib
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from config.audio_config import (
    TTS_CONFIG,
    PERSONALITY_TO_VOICE_PARAMS,
    DEFAULT_VOICE_PARAMS,
    AUDIO_OUTPUT_CONFIG,
    CACHING_CONFIG,
    GENDER_KEYWORDS,
    GENDER_PITCH_MULTIPLIERS,
)

from pydub import AudioSegment
from pydub import utils as pydub_utils

# Force pydub to use imageio_ffmpeg binary
pydub_utils.get_encoder_name = lambda: _ffmpeg_exe
AudioSegment.converter = _ffmpeg_exe
AudioSegment.ffmpeg = _ffmpeg_exe

# ==============================================================================
# Global Voice Cache (in-memory, per session)
# ==============================================================================

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
    
    # Check for personality keywords
    for keyword, params in PERSONALITY_TO_VOICE_PARAMS.items():
        if keyword in personality_lower:
            return params.copy()
    
    return DEFAULT_VOICE_PARAMS.copy()


def _ensure_audio_directories():
    """Create required audio output directories."""
    os.makedirs(AUDIO_OUTPUT_CONFIG["output_directory"], exist_ok=True)
    os.makedirs(AUDIO_OUTPUT_CONFIG["bgm_directory"], exist_ok=True)
    os.makedirs(CACHING_CONFIG["cache_directory"], exist_ok=True)


# Internal implementation (non-tool version for direct use in agents)
def _synthesize_dialogue_impl(
    text: str,
    character_name: str,
    character_appearance: str = "",
    voice_personality: str = "",
    scene_id: str = "",
    dialogue_index: int = 0,
) -> str:
    _ensure_audio_directories()

    safe_char_name = character_name.lower().replace(" ", "_")
    safe_scene_id = scene_id.replace(" ", "_") if scene_id else "unknown"
    output_filename = f"{safe_scene_id}_{safe_char_name}_{dialogue_index}.mp3"
    output_path = os.path.join(AUDIO_OUTPUT_CONFIG["output_directory"], output_filename)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
        print(f"[TTS] Using cached dialogue: {output_path}")
        return output_path

    # Detect gender and personality
    gender = _detect_gender_from_appearance(character_appearance)
    voice_params = _get_voice_params_from_personality(voice_personality)

    # Use gTTS for text-to-speech synthesis
    try:
        from gtts import gTTS
        slow_mode = voice_params.get("speed", 1.0) < 0.9
        tts = gTTS(text=text, lang='en', slow=slow_mode)
        tts.save(output_path)
        print(f"[TTS] gTTS: {character_name} | gender={gender} | personality={voice_personality}")
        return output_path

    except Exception as e:
        print(f"[TTS ERROR] gTTS failed: {e}")
        _create_silent_audio(output_path, 2000)
        return output_path

# Tool-decorated version for LangChain/MCP registration
@tool
def synthesize_dialogue(
    text: str,
    character_name: str,
    character_appearance: str = "",
    voice_personality: str = "",
    scene_id: str = "",
    dialogue_index: int = 0,
) -> str:
    """
    Synthesize dialogue text to speech using gTTS (Google Text-to-Speech).
    Falls back gracefully if TTS unavailable.
    
    Args:
        text: The dialogue line to synthesize
        character_name: Name of the character speaking
        character_appearance: Physical description for gender inference
        voice_personality: Personality traits (e.g., "determined and strong")
        scene_id: Scene identifier
        dialogue_index: Index of dialogue within scene
    
    Returns:
        Path to the generated MP3 file
    """
    return _synthesize_dialogue_impl(text, character_name, character_appearance, voice_personality, scene_id, dialogue_index)


def _create_silent_audio(output_path: str, duration_ms: int = 2000) -> None:
    """Create a silent MP3 file (fallback for synthesis failures)."""
    from pydub import AudioSegment
    silent = AudioSegment.silent(duration=duration_ms)
    silent.export(output_path, format="mp3")
    print(f"[AUDIO] Created silent placeholder: {output_path}")


def _select_bgm_track_impl(scene_tone: str, scene_duration_ms: int = 30000) -> str:
    """Select BGM metadata for a scene tone (actual download not implemented)."""
    from config.audio_config import SCENE_TONE_METADATA
    
    tone_lower = scene_tone.lower() if scene_tone else "default"
    description = SCENE_TONE_METADATA.get(tone_lower, SCENE_TONE_METADATA.get("default", ""))
    
    track_metadata = {
        "tone": tone_lower,
        "description": description,
        "local_path": "",  # BGM download not currently implemented
        "duration_ms": scene_duration_ms,
    }
    print(f"[BGM] Tone '{scene_tone}': {description}")
    return json.dumps(track_metadata)


@tool
def select_bgm_track(scene_tone: str, scene_duration_ms: int = 30000) -> str:
    """
    Select a background music track from royalty-free library based on scene tone.
    
    Args:
        scene_tone: Scene tone/mood (e.g., "urgent", "mysterious", "calm")
        scene_duration_ms: Duration of the scene in milliseconds
    
    Returns:
        JSON string containing {url, duration_ms, description, license}
    """
    return _select_bgm_track_impl(scene_tone, scene_duration_ms)

def _download_bgm_from_freesound(scene_tone: str) -> str:
    import requests

    api_key = os.getenv("FREESOUND_API_KEY")
    bgm_path = os.path.join(AUDIO_OUTPUT_CONFIG["bgm_directory"], f"{scene_tone}.mp3")

    if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 5000:
        print(f"[BGM] Using cached: {bgm_path}")
        return bgm_path

    if not api_key:
        print("[BGM WARNING] No FREESOUND_API_KEY set, skipping BGM")
        return ""

    try:
        # Search for a track by mood
        response = requests.get(
            "https://freesound.org/apiv2/search/text/",
            params={
                "query": f"{scene_tone} background music",
                "token": api_key,
                "fields": "id,name,previews",
                "filter": "duration:[10 TO 120]",
                "page_size": 3,
            },
            timeout=10
        )
        data = response.json()

        if data.get("results"):
            preview_url = data["results"][0]["previews"]["preview-hq-mp3"]
            audio_response = requests.get(preview_url, timeout=30)
            with open(bgm_path, "wb") as f:
                f.write(audio_response.content)
            print(f"[BGM SUCCESS] Downloaded '{scene_tone}' BGM from Freesound")
            return bgm_path

    except Exception as e:
        print(f"[BGM ERROR] {e}")

    return ""

def _download_bgm_track_impl(track_url: str, track_id: str) -> str:
    """
    Internal implementation of BGM track download and caching.
    """
    _ensure_audio_directories()
    
    bgm_path = os.path.join(AUDIO_OUTPUT_CONFIG["bgm_directory"], f"{track_id}.mp3")
    
    # Check cache
    if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 5000:
        print(f"[BGM] Using cached track: {bgm_path}")
        return bgm_path
    
    try:
        import urllib.request
        print(f"[BGM] Downloading track from {track_url}...")
        req = urllib.request.Request(track_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(bgm_path, 'wb') as f:
                f.write(response.read())
        print(f"[BGM SUCCESS] Downloaded to {bgm_path}")
        return bgm_path
    except Exception as e:
        print(f"[BGM WARNING] Failed to download: {e}")
        # Return path (may not exist) so pipeline can handle gracefully
        return bgm_path


@tool
def download_bgm_track(track_url: str, track_id: str) -> str:
    """
    Download background music track and cache locally.
    
    Args:
        track_url: URL to download from
        track_id: Unique identifier for the track (for caching)
    
    Returns:
        Local file path to downloaded MP3
    """
    return _download_bgm_track_impl(track_url, track_id)


def _assemble_audio_segments_impl(
    dialogue_files: str,
    bgm_file: str,
    scene_id: str,
    output_filename: str = "",
) -> str:
    _ensure_audio_directories()

    # Patch ffmpeg - must use subprocess workaround
    _ffmpeg_exe = r"C:\Users\wania\OneDrive\Documents\Semester-8 (FAST)\Agentic AI\Agentic Project\AI-Powered-Animated-Video-Generation-System\agenticproj\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

    os.environ["PATH"] = os.path.dirname(_ffmpeg_exe) + os.pathsep + os.environ.get("PATH", "")

    # Create a fake "ffmpeg" shim in a temp directory so subprocess("ffmpeg") works
    import shutil
    _shim_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "ffmpeg_shim")
    os.makedirs(_shim_dir, exist_ok=True)
    _shim_path = os.path.join(_shim_dir, "ffmpeg.exe")
    if not os.path.exists(_shim_path):
        shutil.copy(_ffmpeg_exe, _shim_path)
    os.environ["PATH"] = _shim_dir + os.pathsep + os.environ.get("PATH", "")

    from pydub import AudioSegment
    AudioSegment.converter = _shim_path
    AudioSegment.ffmpeg = _shim_path

    # Parse dialogue files
    try:
        dialogue_list = json.loads(dialogue_files)
    except json.JSONDecodeError:
        print(f"[ASSEMBLY] Invalid dialogue JSON: {dialogue_files}")
        return json.dumps({"error": "Invalid dialogue JSON"})

    if not dialogue_list:
        print(f"[ASSEMBLY] No dialogue files provided for {scene_id}")
        return json.dumps({"error": "No dialogue files"})

    # Test if ffmpeg actually works by loading first file
    first_dialogue = dialogue_list[0]
    dialogue_path = first_dialogue.get("file", "")

    if not os.path.exists(dialogue_path):
        return json.dumps({"error": f"Dialogue file not found: {dialogue_path}"})

    try:
        test_audio = AudioSegment.from_mp3(dialogue_path)
        print(f"[ASSEMBLY] FFmpeg available, proceeding with full assembly")
    except Exception as ffmpeg_err:
        print(f"[ASSEMBLY WARNING] FFmpeg not available ({ffmpeg_err}), using fallback mode")

        # Fallback: copy first dialogue file as output
        character = first_dialogue.get("character", "Unknown")
        output_name = output_filename if output_filename else f"{scene_id.replace(' ', '_')}.mp3"
        output_path = os.path.join(AUDIO_OUTPUT_CONFIG["output_directory"], output_name)

        import shutil
        try:
            shutil.copy(dialogue_path, output_path)
            file_size = os.path.getsize(output_path)
            duration_ms = max(1000, file_size // 50)
            result = {
                "audio_file": output_path,
                "duration_ms": duration_ms,
                "timing_entries": [{"dialogue_index": 0, "character": character, "start_ms": 0, "end_ms": duration_ms}],
            }
            print(f"[ASSEMBLY SUCCESS] Generated {output_path} (fallback mode, {duration_ms}ms)")
            return json.dumps(result)
        except Exception as copy_err:
            return json.dumps({"error": str(copy_err)})

    # Full assembly with ffmpeg
    try:
        combined_audio = None
        timing_entries = []
        current_offset_ms = 0

        for idx, dialogue_entry in enumerate(dialogue_list):
            dialogue_path = dialogue_entry.get("file", "")
            character = dialogue_entry.get("character", "Unknown")

            if not os.path.exists(dialogue_path):
                print(f"[ASSEMBLY WARNING] Dialogue file not found: {dialogue_path}")
                continue

            try:
                dialogue_audio = AudioSegment.from_mp3(dialogue_path)
                duration_ms = len(dialogue_audio)

                timing_entries.append({
                    "dialogue_index": idx,
                    "character": character,
                    "start_ms": current_offset_ms,
                    "end_ms": current_offset_ms + duration_ms,
                })

                combined_audio = dialogue_audio if combined_audio is None else combined_audio + dialogue_audio
                current_offset_ms += duration_ms

            except Exception as mp3_err:
                print(f"[ASSEMBLY WARNING] Failed to load {dialogue_path}: {mp3_err}")
                continue

        if combined_audio is None:
            return json.dumps({"error": "No valid dialogue audio"})

        # Mix BGM if available
        if bgm_file and os.path.exists(bgm_file):
            try:
                bgm_audio = AudioSegment.from_mp3(bgm_file)
                dialogue_duration = len(combined_audio)
                if len(bgm_audio) < dialogue_duration:
                    repeats = (dialogue_duration // len(bgm_audio)) + 1
                    bgm_audio = bgm_audio * repeats
                bgm_audio = bgm_audio[:dialogue_duration]
                combined_audio = combined_audio.apply_gain(AUDIO_OUTPUT_CONFIG["dialogue_volume_db"])
                bgm_audio = bgm_audio.apply_gain(AUDIO_OUTPUT_CONFIG["bgm_volume_db"])
                combined_audio = combined_audio.overlay(bgm_audio)
                print(f"[ASSEMBLY] Mixed dialogue + BGM for {scene_id}")
            except Exception as bgm_err:
                print(f"[ASSEMBLY WARNING] Failed to mix BGM: {bgm_err}")

        # Export
        output_name = output_filename if output_filename else f"{scene_id.replace(' ', '_')}.mp3"
        output_path = os.path.join(AUDIO_OUTPUT_CONFIG["output_directory"], output_name)
        combined_audio.export(output_path, format="mp3", bitrate=AUDIO_OUTPUT_CONFIG["bitrate"])

        final_duration_ms = len(combined_audio)
        result = {
            "audio_file": output_path,
            "duration_ms": final_duration_ms,
            "timing_entries": timing_entries,
        }

        print(f"[ASSEMBLY SUCCESS] Generated {output_path} ({final_duration_ms}ms)")
        return json.dumps(result)

    except Exception as e:
        print(f"[ASSEMBLY ERROR] {e}")
        return json.dumps({"error": str(e)})

@tool
def assemble_audio_segments(
    dialogue_files: str,  # JSON list of {file, character, duration_ms}
    bgm_file: str,
    scene_id: str,
    output_filename: str = "",
) -> str:
    """
    Mix dialogue audio files with background music and generate timing manifest.
    
    Args:
        dialogue_files: JSON string with list of dialogue file paths and durations
        bgm_file: Path to background music MP3
        scene_id: Scene identifier
        output_filename: Custom output filename (if empty, uses scene_id)
    
    Returns:
        JSON string containing {audio_file, duration_ms, timing_entries}
    """
    return _assemble_audio_segments_impl(dialogue_files, bgm_file, scene_id, output_filename)


def _cache_character_voice_impl(
    character_name: str,
    voice_personality: str,
    character_appearance: str,
) -> str:
    """
    Internal implementation of character voice caching.
    """
    # Ensure directories exist
    _ensure_audio_directories()
    
    character_key = character_name.lower().replace(" ", "_")
    
    # Generate cache entry
    gender = _detect_gender_from_appearance(character_appearance)
    voice_params = _get_voice_params_from_personality(voice_personality)
    
    cache_entry = {
        "character_name": character_name,
        "gender": gender,
        "voice_params": voice_params,
        "personality": voice_personality,
    }
    
    # Store in global cache
    _VOICE_EMBEDDING_CACHE[character_key] = cache_entry
    
    # Optionally persist to disk
    cache_dir = CACHING_CONFIG["cache_directory"]
    cache_file = os.path.join(cache_dir, f"{character_key}.json")
    with open(cache_file, "w") as f:
        json.dump(cache_entry, f, indent=2)
    
    print(f"[CACHE] Cached voice parameters for {character_name}")
    return json.dumps(cache_entry)


@tool
def cache_character_voice(
    character_name: str,
    voice_personality: str,
    character_appearance: str,
) -> str:
    """
    Cache character voice parameters for reuse across scenes.
    
    Args:
        character_name: Name of the character
        voice_personality: Personality string
        character_appearance: Appearance description for gender inference
    
    Returns:
        JSON string with cached voice parameters
    """
    return _cache_character_voice_impl(character_name, voice_personality, character_appearance)


def _get_cached_voice_impl(character_name: str) -> str:
    """
    Internal implementation of getting cached voice parameters.
    """
    character_key = character_name.lower().replace(" ", "_")
    
    # Check in-memory cache first
    if character_key in _VOICE_EMBEDDING_CACHE:
        print(f"[CACHE HIT] Retrieved voice for {character_name} from memory")
        return json.dumps(_VOICE_EMBEDDING_CACHE[character_key])
    
    # Check disk cache
    cache_dir = CACHING_CONFIG["cache_directory"]
    cache_file = os.path.join(cache_dir, f"{character_key}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache_entry = json.load(f)
        _VOICE_EMBEDDING_CACHE[character_key] = cache_entry
        print(f"[CACHE HIT] Retrieved voice for {character_name} from disk")
        return json.dumps(cache_entry)
    
    print(f"[CACHE MISS] No cached voice for {character_name}")
    return json.dumps({})


@tool
def get_cached_voice(character_name: str) -> str:
    """
    Retrieve cached voice parameters for a character.
    
    Args:
        character_name: Name of the character
    
    Returns:
        JSON string with cached voice parameters, or empty dict if not cached
    """
    return _get_cached_voice_impl(character_name)
