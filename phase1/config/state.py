from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- Phase 1: Scripting & Character Models ---

class DialogueItem(BaseModel):
    speaker: str
    line: str

class Scene(BaseModel):
    scene_id: str
    heading: str
    action: str
    dialogue: List[DialogueItem]
    visual_cues: str
    tone: str = "neutral"
    duration: int = 10 # seconds

class CharacterModel(BaseModel):
    name: str
    appearance: str
    traits: Dict[str, Any] = {}
    role: str = "supporting"

class FullScript(BaseModel):
    story: str
    scenes: List[Scene]
    characters: List[CharacterModel]

# Aliases for backward compatibility
SceneManifest = Scene
CharacterProfile = CharacterModel
ScriptOutput = FullScript

# --- Phase 2: Audio Models ---

class AudioTask(BaseModel):
    task_id: str
    scene_id: str
    character: str
    text: str
    voice_params: Dict[str, Any] = {}

class TimingSegment(BaseModel):
    character: str
    text: str
    start_ms: int
    end_ms: int
    audio_file: Optional[str] = None

class TimingManifestEntry(BaseModel):
    scene_id: str
    audio_file: str
    duration_ms: int
    segments: List[TimingSegment]

# --- Agentic Graph State ---

class AgenticState(TypedDict):
    # Workflow control
    mode: str  # "auto" or "manual"
    run_dir: str # Dynamic run directory (e.g. outputs/6MAY-210AM-RUN)
    
    # Phase 1: Script State
    prompt: str
    raw_script: str
    story: str
    scene_manifest: List[Scene]
    character_profiles: Dict[str, Dict[str, Any]] # {name: {appearance, traits}}
    validation_passed: bool
    hitl_approved: bool
    
    # Phase 2: Audio State
    audio_manifest: List[AudioTask]
    audio_files: Dict[str, str]
    bgm_manifest: Dict[str, str]
    timing_manifest: Dict[str, TimingManifestEntry]
    character_voice_cache: Dict[str, Any]
    audio_output_path: str
    
    # Phase 3: Video State
    phase3_output: Optional[Any]
    final_video_path: Optional[str]
