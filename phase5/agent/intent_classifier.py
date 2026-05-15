"""
Phase 5: Edit Intent Classifier
Uses LangGraph + Groq to classify free-text edit commands into structured intent objects.
"""

import json
from typing import Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict


# ─── Pydantic Schema for Structured Intent Output ───────────────────────────

class EditIntent(BaseModel):
    intent: str = Field(description="Short action name, e.g. change_voice_tone")
    target: str = Field(description="One of: audio, video_frame, video, script")
    scope: Optional[str] = Field(default=None, description="e.g. character:Narrator, scene:2")
    parameters: dict = Field(default_factory=dict, description="Extra params like tone, speed, filter")
    confidence: float = Field(default=1.0, description="0.0 to 1.0")


# ─── LangGraph State ─────────────────────────────────────────────────────────

class ClassifierState(TypedDict):
    query: str
    intent: Optional[dict]
    error: Optional[str]


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an intelligent edit intent classifier for an AI video generation system.

Given a user's free-text edit request, you must output a JSON object with this exact structure:
{
  "intent": "<short_action_name>",
  "target": "<audio|video_frame|video|script>",
  "scope": "<optional scope like character:Name or scene:2>",
  "parameters": { <optional key-value pairs relevant to the edit> },
  "confidence": <0.0 to 1.0>
}

Target rules:
- "audio" → voice tone, TTS, background music, sound effects
- "video_frame" → scene image, character appearance, lighting, color, visual style, filters
- "video" → subtitles, speed, transitions, compositing, final export
- "script" → story, plot, dialogue, regenerate, rewrite

Examples:
- "Change voice tone to whisper" → {"intent":"change_voice_tone","target":"audio","scope":null,"parameters":{"tone":"whispered"},"confidence":0.95}
- "Make the scene darker" → {"intent":"adjust_scene_brightness","target":"video_frame","scope":null,"parameters":{"filter":"darken","brightness":-50},"confidence":0.9}
- "Add background music" → {"intent":"add_background_music","target":"audio","scope":null,"parameters":{"action":"add_bgm"},"confidence":0.95}
- "Remove the subtitle" → {"intent":"remove_subtitles","target":"video","scope":null,"parameters":{"subtitles":false},"confidence":0.98}
- "Change character design for Narrator" → {"intent":"change_character_design","target":"video_frame","scope":"character:Narrator","parameters":{},"confidence":0.92}
- "Speed up scene 2" → {"intent":"adjust_scene_speed","target":"video","scope":"scene:2","parameters":{"speed_multiplier":1.5},"confidence":0.9}
- "Regenerate the script" → {"intent":"regenerate_script","target":"script","scope":null,"parameters":{},"confidence":0.99}
- "Apply sepia filter" → {"intent":"apply_filter","target":"video_frame","scope":null,"parameters":{"filter":"sepia"},"confidence":0.97}
- "Make voice sound angry" → {"intent":"change_voice_emotion","target":"audio","scope":null,"parameters":{"emotion":"angry"},"confidence":0.93}
- "Add blur to background" → {"intent":"apply_filter","target":"video_frame","scope":null,"parameters":{"filter":"blur","region":"background"},"confidence":0.88}

IMPORTANT: Return ONLY the JSON object, no markdown, no explanation.
"""


# ─── LangGraph Nodes ─────────────────────────────────────────────────────────

def classify_intent(state: ClassifierState) -> ClassifierState:
    """Call Groq LLM to classify the edit intent."""
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Edit request: {state['query']}")
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        intent_data = json.loads(raw)
        # Validate with Pydantic
        intent = EditIntent(**intent_data)
        return {"query": state["query"], "intent": intent.model_dump(), "error": None}

    except Exception as e:
        return {"query": state["query"], "intent": None, "error": str(e)}


def validate_intent(state: ClassifierState) -> ClassifierState:
    """Fallback: if LLM failed, produce a default unknown intent."""
    if state.get("error") or not state.get("intent"):
        default = EditIntent(
            intent="unknown",
            target="video",
            scope=None,
            parameters={"raw_query": state["query"]},
            confidence=0.0
        )
        return {"query": state["query"], "intent": default.model_dump(), "error": None}
    return state


# ─── Build LangGraph ─────────────────────────────────────────────────────────

def build_classifier_graph():
    graph = StateGraph(ClassifierState)
    graph.add_node("classify", classify_intent)
    graph.add_node("validate", validate_intent)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "validate")
    graph.add_edge("validate", END)

    return graph.compile()


# ─── Public API ──────────────────────────────────────────────────────────────

_graph = None

def classify_edit_query(query: str) -> EditIntent:
    """
    Classify a free-text edit query and return a structured EditIntent.
    
    Example:
        intent = classify_edit_query("Make the scene darker")
        # intent.target == "video_frame"
    """
    global _graph
    if _graph is None:
        _graph = build_classifier_graph()

    result = _graph.invoke({"query": query, "intent": None, "error": None})
    return EditIntent(**result["intent"])
