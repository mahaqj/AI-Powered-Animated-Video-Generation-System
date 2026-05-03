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
