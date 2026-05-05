import json
import os
from pathlib import Path
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from phase1.config.state import AgenticState
from phase1.agents import scriptwriter_node, validator_node, hitl_node, character_designer_node
from phase2.agents import audio_synthesizer_node, bgm_selector_node, audio_assembler_node
from phase3.agents import video_generator_node

def assemble_fullscript_node(state: AgenticState) -> Dict[str, Any]:
    """Phase 2 node: Finalizes script manifest with audio paths."""
    print("--- ACT: Assembler (FullScript) ---")
    return {}

def memory_commit_node(state: AgenticState) -> Dict[str, Any]:
    """Final node: Persists all manifests to the run directory."""
    print("--- ACT: Memory Commit ---")
    
    run_dir = Path(state.get("run_dir", "outputs/default"))
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Save Scene Manifest
    scene_manifest = state.get("scene_manifest", [])
    if scene_manifest:
        manifest_path = run_dir / "scene_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump([s.model_dump() if hasattr(s, 'model_dump') else s for s in scene_manifest], f, indent=4)
            
    # 2. Save Timing Manifest
    timing_manifest = state.get("timing_manifest", {})
    if timing_manifest:
        timing_path = run_dir / "timing_manifest.json"
        timing_output = {}
        for scene_id, entry in timing_manifest.items():
            timing_output[scene_id] = entry.model_dump() if hasattr(entry, 'model_dump') else entry
        with open(timing_path, "w") as f:
            json.dump(timing_output, f, indent=4, default=str)
        print(f"Audio manifest persisted for {len(timing_manifest)} scenes")

    # 3. Save Character Profiles
    character_profiles = state.get("character_profiles", {})
    if character_profiles:
        char_path = run_dir / "character_profiles.json"
        with open(char_path, "w") as f:
            json.dump(character_profiles, f, indent=4)

    # Log Final Video
    final_video = state.get("final_video_path")
    if final_video:
        print(f"--- SUCCESS: Final Video Generated at {final_video} ---")
    else:
        print(f"--- NOTICE: Run complete. Manifests saved in {run_dir} ---")

    return {"final_output_path": str(run_dir)}

def build_graph():
    """Build the complete LangGraph workflow."""
    graph_builder = StateGraph(AgenticState)

    # Add Phase 1 Nodes
    graph_builder.add_node("scriptwriter", scriptwriter_node)
    graph_builder.add_node("validator", validator_node)
    graph_builder.add_node("hitl", hitl_node)
    graph_builder.add_node("character_designer", character_designer_node)
    
    # Add Phase 2 Nodes
    graph_builder.add_node("audio_synthesizer", audio_synthesizer_node)
    graph_builder.add_node("bgm_selector", bgm_selector_node)
    graph_builder.add_node("audio_assembler", audio_assembler_node)
    
    # Add Finalization Nodes
    graph_builder.add_node("assembler", assemble_fullscript_node)
    graph_builder.add_node("video_generator", video_generator_node)
    graph_builder.add_node("memory_commit", memory_commit_node)

    # Define Conditional Routing Logic
    def router(state: AgenticState):
        if state.get("mode") == "manual":
            return "validator"
        return "scriptwriter"

    def validation_router(state: AgenticState):
        if state.get("validation_passed"):
            return "hitl"
        else:
            if state.get("mode") == "manual":
                return END
            return "scriptwriter"

    def hitl_router(state: AgenticState):
        if state.get("hitl_approved"):
            return "character_designer"
        return END

    # Add Edges
    graph_builder.add_conditional_edges(START, router)
    graph_builder.add_edge("scriptwriter", "validator")
    graph_builder.add_conditional_edges("validator", validation_router)
    graph_builder.add_conditional_edges("hitl", hitl_router)
    
    # Phase 2: Audio Parallel Nodes
    graph_builder.add_edge("character_designer", "audio_synthesizer")
    graph_builder.add_edge("character_designer", "bgm_selector")
    
    # Audio Convergence
    graph_builder.add_edge("audio_synthesizer", "audio_assembler")
    graph_builder.add_edge("bgm_selector", "audio_assembler")
    
    # Final Flow
    graph_builder.add_edge("audio_assembler", "assembler")
    graph_builder.add_edge("assembler", "video_generator")
    graph_builder.add_edge("video_generator", "memory_commit")
    graph_builder.add_edge("memory_commit", END)

    return graph_builder.compile()
