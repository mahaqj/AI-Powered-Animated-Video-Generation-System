from langgraph.graph import StateGraph, END, START
from state import AgenticState
from agents import (
    scriptwriter_node, 
    validator_node, 
    hitl_node, 
    character_designer_node, 
    image_synth_node, 
    assemble_fullscript_node,
    memory_commit_node
)

def build_graph():
    graph_builder = StateGraph(AgenticState)

    # Add Nodes
    graph_builder.add_node("scriptwriter", scriptwriter_node)
    graph_builder.add_node("validator", validator_node)
    graph_builder.add_node("hitl", hitl_node)
    graph_builder.add_node("character_designer", character_designer_node)
    graph_builder.add_node("image_synth", image_synth_node)
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
    graph_builder.add_edge("character_designer", "image_synth")
    graph_builder.add_edge("image_synth", "assembler")
    graph_builder.add_edge("assembler", "memory_commit")
    graph_builder.add_edge("memory_commit", END)

    return graph_builder.compile()

# Example usage
# app_workflow = build_graph()
