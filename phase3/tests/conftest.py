import pytest
from pathlib import Path
from phase3.schemas import CharacterDef, SceneDef, DialogueLine, PipelineInput, StoryDef, TimingManifest, SceneAudioManifest, DialogueSegment, BackgroundMusic

@pytest.fixture
def sample_character():
    return CharacterDef(
        id="char_001",
        name="Aria",
        role="Protagonist",
        visual_description="Young woman with silver hair",
        voice_personality="calm and thoughtful"
    )

@pytest.fixture
def sample_scene():
    return SceneDef(
        scene_id="scene_001",
        sequence=1,
        setting="Mars surface",
        mood="epic",
        duration_seconds=10.0,
        visual_prompt="Vast red desert landscape",
        dialogue=[
            DialogueLine(character_id="char_001", line="It's beautiful out here.", emotion="awe")
        ]
    )

@pytest.fixture
def sample_pipeline_input(sample_scene, sample_character):
    scene2 = sample_scene.model_copy(update={"scene_id": "scene_002", "sequence": 2, "mood": "mysterious"})
    return PipelineInput(
        story=StoryDef(title="Mars Odyssey", genre="Sci-Fi", tone="Epic", total_duration_seconds=20.0),
        scenes=[sample_scene, scene2],
        characters=[sample_character]
    )

@pytest.fixture
def sample_timing_manifest(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    dummy_audio = audio_dir / "test.mp3"
    dummy_audio.write_bytes(b"dummy mp3 content")
    
    return TimingManifest(
        scenes=[
            SceneAudioManifest(
                scene_id="scene_001",
                audio_file=str(dummy_audio),
                start_ms=0,
                end_ms=10000,
                dialogue_segments=[
                    DialogueSegment(character_id="char_001", audio_file=str(dummy_audio), start_ms=1000, end_ms=5000)
                ]
            ),
            SceneAudioManifest(
                scene_id="scene_002",
                audio_file=str(dummy_audio),
                start_ms=10000,
                end_ms=20000,
                dialogue_segments=[]
            )
        ],
        background_music=BackgroundMusic(audio_file=str(dummy_audio), volume=0.3)
    )

@pytest.fixture
def tmp_output_dir(tmp_path):
    out = tmp_path / "outputs"
    out.mkdir()
    (out / "images").mkdir()
    (out / "clips").mkdir()
    (out / "final").mkdir()
    return out
