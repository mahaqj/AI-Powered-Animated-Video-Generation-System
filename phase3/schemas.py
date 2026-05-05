from pydantic import BaseModel, ConfigDict, Field
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

class DialogueSegment(BaseModel):
    character_id: str
    audio_file: str
    start_ms: int
    end_ms: int

class SceneAudioManifest(BaseModel):
    scene_id: str
    audio_file: str
    start_ms: int
    end_ms: int
    dialogue_segments: List[DialogueSegment]
    bgm_file: Optional[str] = None # Added for per-scene BGM support

class BackgroundMusic(BaseModel):
    audio_file: str
    volume: float = 0.3

class TimingManifest(BaseModel):
    scenes: List[SceneAudioManifest]
    background_music: Optional[BackgroundMusic] = None
    
    def get_scene(self, scene_id: str) -> Optional[SceneAudioManifest]:
        return next((s for s in self.scenes if s.scene_id == scene_id), None)

class DialogueLine(BaseModel):
    character_id: str
    line: str
    emotion: str

class CharacterDef(BaseModel):
    id: str
    name: str
    role: str
    visual_description: str
    voice_personality: str

class SceneDef(BaseModel):
    scene_id: str
    sequence: int
    setting: str
    mood: str
    duration_seconds: float
    visual_prompt: str
    dialogue: List[DialogueLine]

class StoryDef(BaseModel):
    title: str
    genre: str
    tone: str
    total_duration_seconds: float

class PipelineInput(BaseModel):
    story: StoryDef
    scenes: List[SceneDef]
    characters: List[CharacterDef]
    
    def get_character(self, character_id: str) -> Optional[CharacterDef]:
        return next((c for c in self.characters if c.id == character_id), None)
        
    def get_scene(self, scene_id: str) -> Optional[SceneDef]:
        return next((s for s in self.scenes if s.scene_id == scene_id), None)

class GeneratedScene(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    scene_id: str
    sequence: int
    image_path: Path
    clip_path: Path
    duration_seconds: float
    audio_path: Path
    bgm_path: Optional[Path] = None # Added for persistence

class Phase3Output(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    pipeline_input: PipelineInput
    generated_scenes: List[GeneratedScene]
    final_video_path: Path
    version: int = 1
    created_at: datetime
