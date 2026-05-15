"""
Phase 5 Tests: Edit Intent Classifier
Covers 10+ edit query types as required by the project spec.

Run with:
    pytest phase5/tests/test_intent_classifier.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from phase5.agent.intent_classifier import classify_edit_query, EditIntent


# ─── Mock LLM responses for deterministic testing ────────────────────────────

MOCK_RESPONSES = {
    "Change voice tone to whisper": '{"intent":"change_voice_tone","target":"audio","scope":"character:Narrator","parameters":{"tone":"whispered"},"confidence":0.95}',
    "Make the scene darker": '{"intent":"adjust_scene_brightness","target":"video_frame","scope":null,"parameters":{"filter":"darken","brightness":-50},"confidence":0.92}',
    "Add background music": '{"intent":"add_background_music","target":"audio","scope":null,"parameters":{"action":"add_bgm"},"confidence":0.95}',
    "Remove the subtitle": '{"intent":"remove_subtitles","target":"video","scope":null,"parameters":{"subtitles":false},"confidence":0.98}',
    "Change character design for Hero": '{"intent":"change_character_design","target":"video_frame","scope":"character:Hero","parameters":{},"confidence":0.92}',
    "Speed up scene 2": '{"intent":"adjust_scene_speed","target":"video","scope":"scene:2","parameters":{"speed_multiplier":1.5},"confidence":0.90}',
    "Regenerate the script": '{"intent":"regenerate_script","target":"script","scope":null,"parameters":{},"confidence":0.99}',
    "Apply sepia filter": '{"intent":"apply_filter","target":"video_frame","scope":null,"parameters":{"filter":"sepia"},"confidence":0.97}',
    "Make the voice sound angry": '{"intent":"change_voice_emotion","target":"audio","scope":null,"parameters":{"emotion":"angry"},"confidence":0.93}',
    "Add blur to the background": '{"intent":"apply_filter","target":"video_frame","scope":null,"parameters":{"filter":"blur","region":"background"},"confidence":0.88}',
    "Change the transition to dissolve": '{"intent":"change_transition","target":"video","scope":null,"parameters":{"transition":"dissolve"},"confidence":0.91}',
    "Rewrite the dialogue for scene 3": '{"intent":"regenerate_script","target":"script","scope":"scene:3","parameters":{"scope":"dialogue"},"confidence":0.85}',
}


def _mock_llm(query: str):
    """Return a mock LLM response for a given query."""
    mock_response = MagicMock()
    mock_response.content = MOCK_RESPONSES.get(query, '{"intent":"unknown","target":"video","scope":null,"parameters":{},"confidence":0.0}')
    return mock_response


# ─── Test Cases ───────────────────────────────────────────────────────────────

class TestIntentClassifier:

    def _classify(self, query: str) -> EditIntent:
        """Helper: classify with mocked LLM."""
        with patch("phase5.agent.intent_classifier.ChatGroq") as MockLLM:
            instance = MockLLM.return_value
            instance.invoke.return_value = _mock_llm(query)
            # Reset the cached graph so it uses mock
            import phase5.agent.intent_classifier as mod
            mod._graph = None
            return classify_edit_query(query)

    def test_change_voice_tone(self):
        intent = self._classify("Change voice tone to whisper")
        assert intent.target == "audio"
        assert intent.intent == "change_voice_tone"
        assert intent.parameters.get("tone") == "whispered"
        assert intent.confidence > 0.9

    def test_make_scene_darker(self):
        intent = self._classify("Make the scene darker")
        assert intent.target == "video_frame"
        assert "darken" in intent.intent or intent.parameters.get("filter") == "darken"

    def test_add_background_music(self):
        intent = self._classify("Add background music")
        assert intent.target == "audio"
        assert intent.intent == "add_background_music"

    def test_remove_subtitles(self):
        intent = self._classify("Remove the subtitle")
        assert intent.target == "video"
        assert "subtitle" in intent.intent

    def test_change_character_design(self):
        intent = self._classify("Change character design for Hero")
        assert intent.target == "video_frame"
        assert intent.scope == "character:Hero"

    def test_speed_up_scene(self):
        intent = self._classify("Speed up scene 2")
        assert intent.target == "video"
        assert intent.scope == "scene:2"
        assert intent.parameters.get("speed_multiplier", 0) > 1.0

    def test_regenerate_script(self):
        intent = self._classify("Regenerate the script")
        assert intent.target == "script"
        assert intent.confidence > 0.9

    def test_apply_sepia_filter(self):
        intent = self._classify("Apply sepia filter")
        assert intent.target == "video_frame"
        assert intent.parameters.get("filter") == "sepia"

    def test_change_voice_emotion(self):
        intent = self._classify("Make the voice sound angry")
        assert intent.target == "audio"
        assert intent.parameters.get("emotion") == "angry"

    def test_blur_filter(self):
        intent = self._classify("Add blur to the background")
        assert intent.target == "video_frame"
        assert intent.parameters.get("filter") == "blur"

    def test_change_transition(self):
        intent = self._classify("Change the transition to dissolve")
        assert intent.target == "video"
        assert intent.parameters.get("transition") == "dissolve"

    def test_rewrite_dialogue(self):
        intent = self._classify("Rewrite the dialogue for scene 3")
        assert intent.target == "script"
        assert "scene:3" in (intent.scope or "")

    def test_output_is_edit_intent_type(self):
        intent = self._classify("Make the scene darker")
        assert isinstance(intent, EditIntent)

    def test_confidence_in_range(self):
        intent = self._classify("Make the scene darker")
        assert 0.0 <= intent.confidence <= 1.0


# ─── Filter Tests (no LLM needed) ────────────────────────────────────────────

class TestImageFilters:

    def test_filter_list_not_empty(self):
        from phase5.filters.image_filters import AVAILABLE_FILTERS
        assert len(AVAILABLE_FILTERS) >= 10

    def test_known_filters_present(self):
        from phase5.filters.image_filters import AVAILABLE_FILTERS
        for f in ["darken", "brighten", "sepia", "grayscale", "blur", "sharpen", "vintage"]:
            assert f in AVAILABLE_FILTERS

    def test_apply_filter_missing_file(self):
        from phase5.filters.image_filters import apply_filter_to_image
        result = apply_filter_to_image("/nonexistent/path.png", "sepia")
        assert result["success"] is False

    def test_apply_filter_empty_dir(self, tmp_path):
        from phase5.filters.image_filters import apply_filter_to_all_scenes
        result = apply_filter_to_all_scenes(str(tmp_path), "sepia")
        assert result["success"] is False
        assert "No images" in result["message"]

    def test_apply_darken_to_real_image(self, tmp_path):
        """Create a small test image and apply filter."""
        import cv2
        import numpy as np
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        img_path = tmp_path / "test.png"
        cv2.imwrite(str(img_path), img)

        from phase5.filters.image_filters import apply_filter_to_image
        result = apply_filter_to_image(str(img_path), "darken")
        assert result["success"] is True

        # Verify it got darker
        result_img = cv2.imread(str(img_path))
        assert result_img.mean() < 128


# ─── State Manager Tests ─────────────────────────────────────────────────────

class TestStateManager:

    def test_snapshot_and_history(self, tmp_path):
        from phase5.state.state_manager import StateManager
        sm = StateManager(run_dir=str(tmp_path))

        state1 = {"title": "My Video", "scenes": [{"id": 1}], "characters": [{"name": "Hero"}]}
        v1 = sm.snapshot("Initial generation", state1)
        assert v1 == 1

        state2 = {"title": "My Video", "scenes": [{"id": 1}], "characters": [{"name": "Hero"}], "bgm_enabled": False}
        v2 = sm.snapshot("Removed BGM", state2)
        assert v2 == 2

        history = sm.history()
        assert len(history) == 2
        assert history[0]["version_label"] == "v1"
        assert history[1]["description"] == "Removed BGM"

    def test_revert_restores_state(self, tmp_path):
        from phase5.state.state_manager import StateManager
        sm = StateManager(run_dir=str(tmp_path))

        state1 = {"title": "Original"}
        state2 = {"title": "Edited"}
        sm.snapshot("v1", state1)
        sm.snapshot("v2", state2)

        restored = sm.revert(1)
        assert restored["title"] == "Original"

    def test_latest_version_id(self, tmp_path):
        from phase5.state.state_manager import StateManager
        sm = StateManager(run_dir=str(tmp_path))
        assert sm.latest_version_id() is None
        sm.snapshot("test", {"x": 1})
        assert sm.latest_version_id() == 1
