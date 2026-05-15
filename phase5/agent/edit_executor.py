"""
Phase 5: Edit Executor
Dispatches edit actions based on classified intent targets.
Integrates with the StateManager for snapshotting before each edit.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional

from phase5.agent.intent_classifier import EditIntent
from phase5.state.state_manager import StateManager
from phase5.filters.image_filters import apply_filter_to_image, apply_filter_to_all_scenes


class EditExecutor:
    """
    Executes edit commands based on a classified EditIntent.
    Always snapshots state before executing so changes are reversible.
    """

    def __init__(self, run_dir: str, state_manager: StateManager):
        """
        Args:
            run_dir: Path to the current pipeline run output directory
                     e.g. outputs/12May-1430PM-RUN/
            state_manager: The StateManager instance for snapshotting
        """
        self.run_dir = Path(run_dir)
        self.sm = state_manager

    # ─── Main dispatch ───────────────────────────────────────────────────────

    def execute(self, intent: EditIntent, current_state: dict) -> dict:
        """
        Execute the edit described by intent.

        Returns:
            dict with keys: success (bool), message (str), updated_state (dict)
        """
        target = intent.target

        if target == "audio":
            return self._edit_audio(intent, current_state)
        elif target == "video_frame":
            return self._edit_video_frame(intent, current_state)
        elif target == "video":
            return self._edit_video(intent, current_state)
        elif target == "script":
            return self._edit_script(intent, current_state)
        else:
            return {"success": False, "message": f"Unknown target: {target}", "updated_state": current_state}

    # ─── Audio edits ─────────────────────────────────────────────────────────

    def _edit_audio(self, intent: EditIntent, state: dict) -> dict:
        """Handle audio-target edits."""
        action = intent.intent
        params = intent.parameters
        updated = json.loads(json.dumps(state))  # deep copy

        if action == "change_voice_tone":
            tone = params.get("tone", "normal")
            # Mark in state so Phase 2 re-runs with new tone
            for char in updated.get("characters", []):
                if intent.scope and f"character:{char.get('name','')}" != intent.scope:
                    continue
                char["voice_tone"] = tone
            message = f"Voice tone updated to '{tone}'. Re-run Phase 2 to apply."

        elif action == "change_voice_emotion":
            emotion = params.get("emotion", "neutral")
            for char in updated.get("characters", []):
                if intent.scope and f"character:{char.get('name','')}" != intent.scope:
                    continue
                char["voice_emotion"] = emotion
            message = f"Voice emotion set to '{emotion}'. Re-run Phase 2 to apply."

        elif action == "add_background_music":
            updated["bgm_enabled"] = True
            updated["bgm_action"] = params.get("action", "add_bgm")
            message = "Background music flag enabled. Re-run Phase 2 to apply."

        elif action == "remove_background_music":
            updated["bgm_enabled"] = False
            message = "Background music disabled."

        else:
            message = f"Audio edit '{action}' recorded. Re-run Phase 2 to apply."

        updated["last_edit"] = {"intent": action, "target": "audio", "params": params}
        return {"success": True, "message": message, "updated_state": updated}

    # ─── Video frame edits (image/filter) ────────────────────────────────────

    def _edit_video_frame(self, intent: EditIntent, state: dict) -> dict:
        """Handle video_frame-target edits using OpenCV filters."""
        action = intent.intent
        params = intent.parameters
        updated = json.loads(json.dumps(state))

        images_dir = self.run_dir / "images"

        if not images_dir.exists():
            return {"success": False, "message": "No images directory found in run output.", "updated_state": state}

        filter_name = params.get("filter", "")
        scope = intent.scope  # e.g. "scene:2"

        if filter_name:
            if scope and scope.startswith("scene:"):
                scene_num = scope.split(":")[1]
                # Apply to a specific scene's image
                scene_images = list(images_dir.glob(f"*scene_{scene_num}*")) + \
                               list(images_dir.glob(f"*{scene_num}*"))
                if scene_images:
                    for img_path in scene_images:
                        result = apply_filter_to_image(str(img_path), filter_name, params)
                        if not result["success"]:
                            return {"success": False, "message": result["message"], "updated_state": state}
                    message = f"Filter '{filter_name}' applied to scene {scene_num} images."
                else:
                    message = f"No images found for scene {scene_num}."
            else:
                # Apply to ALL scene images
                result = apply_filter_to_all_scenes(str(images_dir), filter_name, params)
                message = result["message"]
                if not result["success"]:
                    return {"success": False, "message": message, "updated_state": state}
        elif action == "change_character_design":
            char_name = scope.replace("character:", "") if scope else "all"
            # Mark in state — actual re-generation triggered by re-running Phase 3
            for scene in updated.get("scenes", []):
                if char_name == "all" or char_name in scene.get("characters_present", []):
                    scene["regenerate_image"] = True
            message = f"Character design change for '{char_name}' flagged. Re-run Phase 3 to regenerate images."
        else:
            message = f"Video frame edit '{action}' recorded."

        updated["last_edit"] = {"intent": action, "target": "video_frame", "params": params}
        return {"success": True, "message": message, "updated_state": updated}

    # ─── Full video edits ─────────────────────────────────────────────────────

    def _edit_video(self, intent: EditIntent, state: dict) -> dict:
        """Handle full-video-target edits (subtitles, speed, transitions)."""
        action = intent.intent
        params = intent.parameters
        updated = json.loads(json.dumps(state))

        if action == "remove_subtitles":
            updated["subtitles_enabled"] = False
            message = "Subtitles disabled. Re-run Phase 3 compositing to apply."

        elif action == "add_subtitles":
            updated["subtitles_enabled"] = True
            message = "Subtitles enabled. Re-run Phase 3 compositing to apply."

        elif action == "adjust_scene_speed":
            speed = params.get("speed_multiplier", 1.5)
            scope = intent.scope
            if scope and scope.startswith("scene:"):
                scene_num = int(scope.split(":")[1]) - 1  # 0-indexed
                scenes = updated.get("scenes", [])
                if 0 <= scene_num < len(scenes):
                    scenes[scene_num]["speed_multiplier"] = speed
                    message = f"Speed set to {speed}x for scene {scene_num + 1}. Re-run Phase 3."
                else:
                    message = f"Scene {scene_num + 1} not found."
            else:
                for scene in updated.get("scenes", []):
                    scene["speed_multiplier"] = speed
                message = f"Speed set to {speed}x for all scenes. Re-run Phase 3."

        elif action == "change_transition":
            transition = params.get("transition", "fade")
            updated["transition_style"] = transition
            message = f"Transition style set to '{transition}'. Re-run Phase 3."

        else:
            message = f"Video edit '{action}' recorded. Re-run Phase 3 to apply."

        updated["last_edit"] = {"intent": action, "target": "video", "params": params}
        return {"success": True, "message": message, "updated_state": updated}

    # ─── Script edits ─────────────────────────────────────────────────────────

    def _edit_script(self, intent: EditIntent, state: dict) -> dict:
        """Handle script-target edits. Flags cascade through all phases."""
        action = intent.intent
        params = intent.parameters
        updated = json.loads(json.dumps(state))

        updated["regenerate_script"] = True
        updated["script_edit_params"] = params
        updated["cascade_all"] = True  # Signal to re-run all phases

        message = (
            "Script regeneration flagged. This will cascade through audio and video phases. "
            "Re-run from Phase 1 to apply all changes."
        )
        updated["last_edit"] = {"intent": action, "target": "script", "params": params}
        return {"success": True, "message": message, "updated_state": updated}
