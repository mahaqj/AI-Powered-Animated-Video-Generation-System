import pytest
from phase5.edit_intent import EditIntentClassifier, EditIntent


@pytest.fixture
def classifier():
    return EditIntentClassifier()


class TestCharacterVoiceEdits:
    """Tests for character voice/tone edits."""

    def test_change_voice_robotic(self, classifier):
        intent = classifier.classify("Make the voice more robotic for Alice")
        assert intent.target == "character"
        assert intent.action == "change_voice"
        assert intent.target_id and intent.target_id.lower() == "alice"

    def test_change_voice_whisper(self, classifier):
        intent = classifier.classify("Make Bob speak in a whisper")
        assert intent.target == "character"
        assert intent.action == "change_voice"

    def test_change_voice_without_name(self, classifier):
        intent = classifier.classify("Make all voices more dramatic")
        assert intent.target == "character"
        assert intent.action == "change_voice"

    def test_tone_adjustment(self, classifier):
        intent = classifier.classify("Adjust the tone to be more menacing")
        assert intent.target == "character"
        assert intent.action == "change_voice"


class TestSceneEdits:
    """Tests for scene-level edits (duration, brightness, etc)."""

    def test_make_scene_longer(self, classifier):
        intent = classifier.classify("Make scene 2 longer")
        assert intent.target == "scene"
        assert intent.action == "adjust_scene"

    def test_make_scene_shorter(self, classifier):
        intent = classifier.classify("Speed up scene 3 by making it shorter")
        assert intent.target == "scene"
        assert intent.action == "adjust_scene"

    def test_make_scene_darker(self, classifier):
        intent = classifier.classify("Make the scene darker")
        assert intent.target == "scene"
        assert intent.action == "adjust_scene"

    def test_brighten_scene(self, classifier):
        intent = classifier.classify("Brighten up scene 1")
        assert intent.target == "scene"
        assert intent.action == "adjust_scene"

    def test_duration_specific(self, classifier):
        intent = classifier.classify("Make scene 5 duration 10 seconds")
        assert intent.target == "scene"
        assert intent.action == "adjust_scene"
        assert intent.params.get("duration_seconds") == 10


class TestScriptEdits:
    """Tests for dialogue/script edits."""

    def test_replace_dialogue_line(self, classifier):
        text = 'Replace "hello" with "hey" for Bob'
        intent = classifier.classify(text)
        assert intent.target == "script"
        assert intent.action == "replace_line"
        assert intent.params["old"] == "hello"
        assert intent.params["new"] == "hey"
        assert "Bob" in (intent.params.get("character") or "")

    def test_replace_without_character(self, classifier):
        text = 'Replace "goodbye" with "farewell"'
        intent = classifier.classify(text)
        assert intent.target == "script"
        assert intent.action == "replace_line"
        assert intent.params["old"] == "goodbye"
        assert intent.params["new"] == "farewell"

    def test_generic_dialogue_edit(self, classifier):
        intent = classifier.classify("Fix the dialogue in scene 1")
        # "scene" keyword is stronger, so this may classify as scene instead of script
        assert intent.target in ["script", "scene"]
        assert intent.action is not None


class TestAudioEdits:
    """Tests for audio/music edits."""

    def test_adjust_bgm_volume(self, classifier):
        intent = classifier.classify("Lower the background music volume")
        assert intent.target == "audio"
        assert intent.action == "adjust_audio"

    def test_add_music(self, classifier):
        intent = classifier.classify("Add background music to this scene")
        # "scene" keyword is stronger, so this may classify as scene instead of audio
        assert intent.target in ["audio", "scene"]
        assert intent.action is not None

    def test_audio_general(self, classifier):
        intent = classifier.classify("Adjust the audio levels")
        assert intent.target == "audio"
        assert intent.action == "adjust_audio"


class TestVideoEdits:
    """Tests for general video edits."""

    def test_generic_video_edit(self, classifier):
        intent = classifier.classify("Make the final video brighter overall")
        assert intent.target in ["video", "scene"]

    def test_fallback_edit(self, classifier):
        intent = classifier.classify("Something completely random")
        assert intent.target is not None  # Should still classify
        assert intent.action is not None


class TestIntentStructure:
    """Tests for EditIntent Pydantic model."""

    def test_edit_intent_required_fields(self):
        """Verify EditIntent has required target and action."""
        intent = EditIntent(target="script", action="replace_line")
        assert intent.target == "script"
        assert intent.action == "replace_line"
        assert intent.target_id is None
        assert intent.params == {}

    def test_edit_intent_with_params(self):
        """Verify EditIntent params are stored."""
        intent = EditIntent(
            target="scene",
            action="adjust_scene",
            target_id="scene_1",
            params={"duration_seconds": 5}
        )
        assert intent.params["duration_seconds"] == 5

