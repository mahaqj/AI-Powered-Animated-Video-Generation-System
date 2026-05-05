"""
Phase 2 Agent Nodes: Audio Generation & Integration
Updated to support unified dynamic run directories.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from phase1.config.state import AgenticState, TimingManifestEntry, TimingSegment
from .audio_tools import (
    _synthesize_dialogue_impl,
    _cache_character_voice_impl,
    _select_bgm_track_impl,
    _download_bgm_from_freesound,
    _assemble_audio_segments_impl,
)

def audio_synthesizer_node(state: AgenticState) -> dict:
    """Synthesizes dialogue lines using state['run_dir']."""
    print("--- ACT: Audio Synthesizer ---")
    
    manifest = state.get("scene_manifest", [])
    characters = state.get("character_profiles", {})
    run_dir = state["run_dir"]
    
    audio_manifest = []
    audio_files = {}
    
    for scene in manifest:
        scene_id = scene.scene_id
        for dialogue_idx, dialogue_entry in enumerate(scene.dialogue):
            speaker = dialogue_entry.speaker
            line = dialogue_entry.line
            
            char_data = characters.get(speaker, {})
            appearance = char_data.get("appearance", "")
            voice_personality = char_data.get("traits", {}).get("voice_personality", "")
            
            _cache_character_voice_impl(speaker, voice_personality, appearance, run_dir)
            
            output_path = _synthesize_dialogue_impl(
                text=line,
                character_name=speaker,
                run_dir=run_dir,
                character_appearance=appearance,
                voice_personality=voice_personality,
                scene_id=scene_id,
                dialogue_index=dialogue_idx,
            )
            
            task_id = f"{scene_id}_{dialogue_idx}_{speaker}"
            audio_files[task_id] = output_path
            audio_manifest.append({
                "scene_id": scene_id,
                "dialogue_index": dialogue_idx,
                "character": speaker,
                "audio_file": output_path
            })
            
    return {"audio_manifest": audio_manifest, "audio_files": audio_files}

def bgm_selector_node(state: AgenticState) -> dict:
    """Selects BGM using state['run_dir']."""
    print("--- ACT: BGM Selector ---")
    manifest = state.get("scene_manifest", [])
    run_dir = state["run_dir"]
    bgm_manifest = {}
    
    for scene in manifest:
        tone = scene.tone or "default"
        duration_ms = scene.duration * 1000
        _select_bgm_track_impl(tone, duration_ms)
        bgm_file = _download_bgm_from_freesound(tone, run_dir)
        bgm_manifest[scene.scene_id] = bgm_file
        
    return {"bgm_manifest": bgm_manifest}

def audio_assembler_node(state: AgenticState) -> dict:
    """Assembles audio using state['run_dir']."""
    print("--- ACT: Audio Assembler ---")
    manifest = state.get("scene_manifest", [])
    audio_manifest = state.get("audio_manifest", [])
    bgm_manifest = state.get("bgm_manifest", {})
    run_dir = state["run_dir"]
    
    timing_manifest = {}
    tasks_by_scene = {}
    for task in audio_manifest:
        tasks_by_scene.setdefault(task["scene_id"], []).append(task)
        
    for scene in manifest:
        scene_id = scene.scene_id
        if scene_id not in tasks_by_scene: continue
        
        dialogue_tasks = tasks_by_scene[scene_id]
        dialogue_list = [{"file": t["audio_file"], "character": t["character"]} for t in dialogue_tasks]
        
        result_json = _assemble_audio_segments_impl(
            json.dumps(dialogue_list),
            bgm_manifest.get(scene_id, ""),
            scene_id,
            run_dir
        )
        result = json.loads(result_json)
        
        segments = []
        for te in result.get("timing_entries", []):
            segments.append(TimingSegment(
                character=te["character"],
                text="", # Not needed for timing
                start_ms=te["start_ms"],
                end_ms=te["end_ms"],
                audio_file=dialogue_list[te["dialogue_index"]]["file"]
            ))
            
        timing_manifest[scene_id] = TimingManifestEntry(
            scene_id=scene_id,
            audio_file=result["audio_file"],
            duration_ms=result["duration_ms"],
            segments=segments
        )
        
    return {"timing_manifest": timing_manifest, "audio_output_path": str(Path(run_dir) / "timing_manifest.json")}
