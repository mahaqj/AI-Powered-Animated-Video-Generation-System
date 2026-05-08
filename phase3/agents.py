import asyncio
import logging
import re
from typing import Any, Dict, List
from pathlib import Path

from phase1.config.state import AgenticState
from .pipeline import get_pipeline
from .schemas import (
    PipelineInput, 
    StoryDef, 
    SceneDef, 
    CharacterDef, 
    DialogueLine, 
    TimingManifest, 
    SceneAudioManifest, 
    DialogueSegment,
    BackgroundMusic
)

logger = logging.getLogger("phase3.agents")

def _extract_sequence(scene_id: str) -> int:
    """Extract numeric sequence from scene_id strings like 'scene1' or 'Scene 1'."""
    match = re.search(r'\d+', scene_id)
    if match:
        return int(match.group())
    return 1

def video_generator_node(state: AgenticState) -> Dict[str, Any]:
    """
    Phase 3 Node: Generates images, animates clips, and composites the final video.
    Uses state['run_dir'] for unified output management.
    """
    return asyncio.run(_video_generator_node_async(state))

async def _video_generator_node_async(state: AgenticState) -> Dict[str, Any]:
    """Internal async implementation of Phase 3 Node."""
    print("--- ACT: Video Generator ---")
    
    run_dir = state.get("run_dir")
    
    # 1. Map AgenticState to Phase 3 PipelineInput
    story_def = StoryDef(
        title=state.get("story", "Untitled Story"),
        genre="Action", 
        tone="Dynamic",
        total_duration_seconds=sum(s.duration or 10 for s in state.get("scene_manifest", []))
    )
    
    characters = []
    char_profiles = state.get("character_profiles", {})
    for char_name, profile in char_profiles.items():
        characters.append(CharacterDef(
            id=char_name,
            name=char_name,
            role=profile.get("role", "supporting"),
            visual_description=profile.get("appearance", "A generic character"),
            voice_personality=profile.get("traits", {}).get("voice_personality", "neutral")
        ))
        
    scenes = []
    for s in state.get("scene_manifest", []):
        dialogue = []
        for d in s.dialogue:
            dialogue.append(DialogueLine(
                character_id=d.speaker,
                line=d.line,
                emotion="neutral"
            ))
            
        scenes.append(SceneDef(
            scene_id=s.scene_id,
            sequence=_extract_sequence(s.scene_id),
            setting=s.heading,
            mood=s.tone or "neutral",
            duration_seconds=float(s.duration or 10),
            visual_prompt=s.visual_cues,
            dialogue=dialogue
        ))
        
    pipeline_input = PipelineInput(
        story=story_def,
        scenes=scenes,
        characters=characters
    )
    
    # 2. Map TimingManifest
    p3_scenes = []
    bgm_manifest = state.get("bgm_manifest", {})
    
    timing_manifest_data = state.get("timing_manifest", {})
    for scene_id, entry in timing_manifest_data.items():
        segments = []
        for seg in entry.segments:
            segments.append(DialogueSegment(
                character_id=seg.character,
                audio_file=seg.audio_file or "",
                start_ms=seg.start_ms,
                end_ms=seg.end_ms
            ))
            
        p3_scenes.append(SceneAudioManifest(
            scene_id=scene_id,
            audio_file=entry.audio_file,
            start_ms=0,
            end_ms=entry.duration_ms,
            dialogue_segments=segments,
            bgm_file=bgm_manifest.get(scene_id) # Support per-scene BGM
        ))

    timing_manifest = TimingManifest(
        scenes=p3_scenes,
        background_music=None # Using per-scene BGM instead
    )
    
    # 3. Run Pipeline
    pipeline = get_pipeline()
    try:
        output = await pipeline.run(pipeline_input, timing_manifest, add_subtitles=True, run_dir=run_dir)
        return {
            "phase3_output": output,
            "final_video_path": str(output.final_video_path),
            "final_video_error": None,
        }
    except Exception as e:
        logger.error(f"[Phase 3 Error] Video generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "phase3_output": None,
            "final_video_path": None,
            "final_video_error": str(e),
        }
