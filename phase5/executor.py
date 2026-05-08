from .edit_intent import EditIntent
from phase3.schemas import Phase3Output, CharacterDef, SceneDef
from typing import Optional
import logging

logger = logging.getLogger("phase5.executor")


class EditExecutor:
    """Apply edits to a Phase3Output object in-memory.

    This executor makes small, deterministic modifications to the
    Phase3Output/PipelineInput structure. It does NOT attempt to
    re-run expensive media generation; callers can trigger re-runs
    via existing pipeline endpoints (rerun/partial rerun) if needed.
    """

    @staticmethod
    def apply_edit(state: Phase3Output, intent: EditIntent) -> Phase3Output:
        # operate on a copy-ish — pydantic models are mutable here
        if intent.target == "character" and intent.action == "change_voice":
            name = intent.target_id
            voice = intent.params.get("voice")

            # try matching by id or name
            for c in state.pipeline_input.characters:
                if name and (c.id.lower() == name.lower() or c.name.lower() == name.lower()):
                    if voice:
                        c.voice_personality = voice
                        logger.info(f"Updated voice for character {c.id} -> {voice}")
                        break
            else:
                # if no target specified, apply to all characters
                for c in state.pipeline_input.characters:
                    if voice:
                        c.voice_personality = voice

        if intent.target == "scene" and intent.action == "adjust_scene":
            sid = intent.target_id
            dur = intent.params.get("duration_seconds")
            for s in state.pipeline_input.scenes:
                if sid is None or str(s.sequence) == str(sid) or s.scene_id == sid:
                    if dur:
                        s.duration_seconds = float(dur)
                        logger.info(f"Adjusted duration for scene {s.scene_id} -> {dur}s")
                        # only apply to the matched scene
                        if sid:
                            break

        if intent.target == "script":
            if intent.action == "replace_line":
                old = intent.params.get("old")
                new = intent.params.get("new")
                char = intent.params.get("character")
                for s in state.pipeline_input.scenes:
                    for dl in s.dialogue:
                        if (char is None or dl.character_id.lower() == (char or "").lower()) and old in dl.line:
                            dl.line = dl.line.replace(old, new)
                            logger.info(f"Replaced dialogue in scene {s.scene_id}: '{old}' -> '{new}'")

            elif intent.action == "edit_dialogue":
                # Best-effort: append a note to the first dialogue
                note = intent.params.get("raw")
                if state.pipeline_input.scenes:
                    first = state.pipeline_input.scenes[0]
                    if first.dialogue:
                        first.dialogue[0].line = f"{first.dialogue[0].line} ({note})"

        if intent.target == "audio" and intent.action == "adjust_audio":
            # No-op placeholder: embed intent into pipeline_input.story.tone for traceability
            raw = intent.params.get("raw")
            state.pipeline_input.story.tone = (state.pipeline_input.story.tone or "") + f" | audio_edit: {raw}"

        # bump created_at and leave version for StateManager to set
        from datetime import datetime
        state.created_at = datetime.utcnow()
        return state
