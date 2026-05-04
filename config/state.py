from typing import TypedDict, List, Optional, Dict, Any
from pydantic import BaseModel


class Scene(BaseModel):
    scene_id: str
    heading: str
    action: str
    dialogue: List[Dict[str, str]]
    visual_cues: str
    tone: Optional[str] = None
    duration: Optional[int] = None


class CharacterModel(BaseModel):
    name: str
    role: Optional[str] = None
    voice_personality: Optional[str] = None
    appearance: Optional[str] = None


class FullScript(BaseModel):
    story: str
    scenes: List[Scene]
    characters: List[CharacterModel]


# ==============================================================================
# Phase 2: Audio Models
# ==============================================================================

class AudioSegment(BaseModel):
    """Timing entry for a single dialogue segment in the audio mix."""
    scene_id: str
    dialogue_index: int
    character: str
    start_ms: int  # Start time in milliseconds
    end_ms: int  # End time in milliseconds
    audio_file: Optional[str] = None  # Path to dialogue MP3


class AudioTask(BaseModel):
    """Task to synthesize a single dialogue line."""
    scene_id: str
    dialogue_index: int
    character: str
    dialogue_text: str
    audio_file: Optional[str] = None  # Path to output MP3
    duration_ms: Optional[int] = None  # Duration after synthesis


class TimingManifestEntry(BaseModel):
    """Entry in the timing manifest for a scene's final audio."""
    scene_id: str
    audio_file: str  # Path to final mixed MP3
    duration_ms: int
    dialogue_count: int
    has_bgm: bool
    segments: List[AudioSegment]  # Detailed timing for each dialogue


class AgenticState(TypedDict):
    # Inputs
    mode: str  # "manual" or "auto"
    prompt: Optional[str]
    raw_script: Optional[str]

    # Internal State
    story: Optional[str]
    scene_manifest: List[Scene]
    characters: Optional[List[Dict[str, Any]]]
    validation_passed: bool
    validation_feedback: Optional[str]
    character_profiles: Dict[str, Any]
    image_paths: Dict[str, str]

    # Output signals
    hitl_approved: bool
    final_output_path: str
    
    # Phase 2: Audio State
    audio_manifest: List[AudioTask]  # All dialogue synthesis tasks
    audio_files: Dict[str, str]  # {task_id: file_path}
    bgm_manifest: Dict[str, str]  # {scene_id: bgm_file_path}
    timing_manifest: Dict[str, TimingManifestEntry]  # Final timing per scene
    character_voice_cache: Dict[str, Any]  # Cached voice parameters per character
    audio_output_path: str  # Path to final timing_manifest.json
