import pytest
from datetime import datetime
from pathlib import Path

from phase5.edit_intent import EditIntent
from phase5.executor import EditExecutor
from phase3.schemas import (
    Phase3Output,
    PipelineInput,
    StoryDef,
    SceneDef,
    CharacterDef,
    GeneratedScene,
    DialogueLine,
)


@pytest.fixture
def sample_phase3_output():
    """Create a minimal Phase3Output for testing."""
    story = StoryDef(
        title="Test Story",
        genre="Drama",
        tone="Dramatic",
        total_duration_seconds=30.0
    )

    characters = [
        CharacterDef(
            id="alice",
            name="Alice",
            role="Protagonist",
            visual_description="Young woman",
            voice_personality="Soft, gentle"
        ),
        CharacterDef(
            id="bob",
            name="Bob",
            role="Antagonist",
            visual_description="Older man",
            voice_personality="Deep, menacing"
        ),
    ]

    scenes = [
        SceneDef(
            scene_id="scene_1",
            sequence=1,
            setting="Forest",
            mood="Tense",
            duration_seconds=10.0,
            visual_prompt="Dark forest at sunset",
            dialogue=[
                DialogueLine(character_id="alice", line="What's that?", emotion="Scared"),
                DialogueLine(character_id="bob", line="Hello there.", emotion="Menacing"),
            ]
        ),
        SceneDef(
            scene_id="scene_2",
            sequence=2,
            setting="Castle",
            mood="Epic",
            duration_seconds=20.0,
            visual_prompt="Grand castle under attack",
            dialogue=[
                DialogueLine(character_id="alice", line="We must flee!", emotion="Desperate"),
            ]
        ),
    ]

    pipeline_input = PipelineInput(story=story, characters=characters, scenes=scenes)

    generated_scenes = [
        GeneratedScene(
            scene_id="scene_1",
            sequence=1,
            image_path=Path("/tmp/scene_1.png"),
            clip_path=Path("/tmp/scene_1.mp4"),
            audio_path=Path("/tmp/scene_1_audio.mp3"),
            duration_seconds=10.0,
        ),
        GeneratedScene(
            scene_id="scene_2",
            sequence=2,
            image_path=Path("/tmp/scene_2.png"),
            clip_path=Path("/tmp/scene_2.mp4"),
            audio_path=Path("/tmp/scene_2_audio.mp3"),
            duration_seconds=20.0,
        ),
    ]

    return Phase3Output(
        pipeline_input=pipeline_input,
        generated_scenes=generated_scenes,
        final_video_path=Path("/tmp/final.mp4"),
        version=1,
        created_at=datetime.utcnow()
    )


class TestEditExecutor:
    """Tests for applying edits to Phase3Output."""

    def test_change_character_voice(self, sample_phase3_output):
        """Test changing a character's voice personality."""
        intent = EditIntent(
            target="character",
            action="change_voice",
            target_id="alice",
            params={"voice": "robotic"}
        )

        result = EditExecutor.apply_edit(sample_phase3_output, intent)

        alice = result.pipeline_input.get_character("alice")
        assert alice is not None
        assert alice.voice_personality == "robotic"

    def test_change_scene_duration(self, sample_phase3_output):
        """Test adjusting a scene's duration."""
        intent = EditIntent(
            target="scene",
            action="adjust_scene",
            target_id="1",
            params={"duration_seconds": 15.0}
        )

        result = EditExecutor.apply_edit(sample_phase3_output, intent)

        scene = result.pipeline_input.get_scene("scene_1")
        assert scene is not None
        assert scene.duration_seconds == 15.0

    def test_replace_dialogue_line(self, sample_phase3_output):
        """Test replacing a dialogue line."""
        intent = EditIntent(
            target="script",
            action="replace_line",
            params={
                "old": "What's that?",
                "new": "Who's there?",
                "character": "alice"
            }
        )

        result = EditExecutor.apply_edit(sample_phase3_output, intent)

        scene = result.pipeline_input.get_scene("scene_1")
        assert any("Who's there?" in dl.line for dl in scene.dialogue)

    def test_audio_edit_embeds_in_tone(self, sample_phase3_output):
        """Test that audio edits embed intent in story tone."""
        intent = EditIntent(
            target="audio",
            action="adjust_audio",
            params={"raw": "Lower background music volume"}
        )

        result = EditExecutor.apply_edit(sample_phase3_output, intent)

        assert "audio_edit" in result.pipeline_input.story.tone

    def test_created_at_updates(self, sample_phase3_output):
        """Test that created_at is updated on edit."""
        original_time = sample_phase3_output.created_at
        
        intent = EditIntent(target="character", action="change_voice", target_id="alice")
        result = EditExecutor.apply_edit(sample_phase3_output, intent)

        assert result.created_at >= original_time

    def test_multiple_character_edits_no_target(self, sample_phase3_output):
        """Test changing all characters' voices when no target specified."""
        intent = EditIntent(
            target="character",
            action="change_voice",
            params={"voice": "whisper"}
        )

        result = EditExecutor.apply_edit(sample_phase3_output, intent)

        for char in result.pipeline_input.characters:
            assert char.voice_personality == "whisper"
