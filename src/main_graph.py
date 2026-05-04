import sys
from pathlib import Path

# Add parent directory to path for imports from config/
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END, START
from config.state import AgenticState
from agents import (
    scriptwriter_node, 
    validator_node, 
    hitl_node, 
    character_designer_node, 
    assemble_fullscript_node,
    memory_commit_node,
    audio_synthesizer_node,
    bgm_selector_node,
    audio_assembler_node,
)

def build_graph():
    graph_builder = StateGraph(AgenticState)

    # Add Nodes
    graph_builder.add_node("scriptwriter", scriptwriter_node)
    graph_builder.add_node("validator", validator_node)
    graph_builder.add_node("hitl", hitl_node)
    graph_builder.add_node("character_designer", character_designer_node)
    # Phase 2: Audio Nodes
    graph_builder.add_node("audio_synthesizer", audio_synthesizer_node)
    graph_builder.add_node("bgm_selector", bgm_selector_node)
    graph_builder.add_node("audio_assembler", audio_assembler_node)
    # Phase 1: Finalization
    graph_builder.add_node("assembler", assemble_fullscript_node)
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
            # If manual mode fails validation, we can't auto-rewrite it (or maybe we can? for now, END)
            if state.get("mode") == "manual":
                return END
            return "scriptwriter" # loop back

    def hitl_router(state: AgenticState):
        if state.get("hitl_approved"):
            return "character_designer"
        return END

    # Edges
    graph_builder.add_conditional_edges(START, router)
    graph_builder.add_edge("scriptwriter", "validator")
    graph_builder.add_conditional_edges("validator", validation_router)
    graph_builder.add_conditional_edges("hitl", hitl_router)
    # Phase 2: Audio synthesis (parallel nodes) - skip image_synth
    graph_builder.add_edge("character_designer", "audio_synthesizer")
    graph_builder.add_edge("character_designer", "bgm_selector")
    # Converge audio nodes
    graph_builder.add_edge("audio_synthesizer", "audio_assembler")
    graph_builder.add_edge("bgm_selector", "audio_assembler")
    # Continue to finalization
    graph_builder.add_edge("audio_assembler", "assembler")
    graph_builder.add_edge("assembler", "memory_commit")
    graph_builder.add_edge("memory_commit", END)

    return graph_builder.compile()

# Example usage
# app_workflow = build_graph()
