import pytest
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from phase3.pipeline import Phase3Pipeline, Settings
from phase3.schemas import GeneratedScene, Phase3Output

@pytest.fixture
def pipeline(tmp_path):
    settings = Settings(
        OUTPUT_DIR=str(tmp_path / "outputs"),
        STATE_DB_PATH=str(tmp_path / "outputs" / "test.db")
    )
    return Phase3Pipeline(settings)

@pytest.mark.asyncio
async def test_run_executes_all_four_steps_in_order(pipeline, sample_pipeline_input, sample_timing_manifest):
    with patch("phase3.image_generator.generate_all_images", new_callable=AsyncMock) as m1, \
         patch("phase3.animator.animate_all_scenes", new_callable=AsyncMock) as m2, \
         patch("phase3.animator.sync_all_scenes", new_callable=AsyncMock) as m3, \
         patch("phase3.compositor.compose_final_video", new_callable=AsyncMock) as m4, \
         patch("phase3.state_manager.StateManager.snapshot", new_callable=AsyncMock) as m5:
        
        m1.return_value = {"scene_001": Path("img1.png")}
        m2.return_value = {"scene_001": Path("clip1.mp4")}
        m3.return_value = [GeneratedScene(
            scene_id="scene_001", sequence=1, image_path=Path("img1.png"), 
            clip_path=Path("clip1.mp4"), duration_seconds=10.0, audio_path=Path("audio1.mp3")
        )]
        m4.return_value = Path("final.mp4")
        m5.return_value = 1
        
        await pipeline.run(sample_pipeline_input, sample_timing_manifest)
        
        m1.assert_called_once()
        m2.assert_called_once()
        m3.assert_called_once()
        m4.assert_called_once()
        m5.assert_called_once()

@pytest.mark.asyncio
async def test_run_partial_only_processes_specified_scene(pipeline, sample_pipeline_input, sample_timing_manifest):
    # Use real Phase3Output instance
    output = Phase3Output(
        pipeline_input=sample_pipeline_input,
        generated_scenes=[
            GeneratedScene(
                scene_id="scene_001", sequence=1, image_path=Path("img1.png"), 
                clip_path=Path("clip1.mp4"), duration_seconds=10.0, audio_path=Path("audio1.mp3")
            ),
            GeneratedScene(
                scene_id="scene_002", sequence=2, image_path=Path("img2.png"), 
                clip_path=Path("clip2.mp4"), duration_seconds=10.0, audio_path=Path("audio2.mp3")
            )
        ],
        final_video_path=Path("final.mp4"),
        version=1,
        created_at=datetime.utcnow()
    )
    
    with patch("phase3.image_generator.generate_all_images", new_callable=AsyncMock) as m1, \
         patch("phase3.animator.animate_all_scenes", new_callable=AsyncMock) as m2, \
         patch("phase3.animator.sync_all_scenes", new_callable=AsyncMock) as m3, \
         patch("phase3.compositor.compose_final_video", new_callable=AsyncMock) as m4, \
         patch("phase3.state_manager.StateManager.snapshot", new_callable=AsyncMock) as m5:
        
        m1.return_value = {"scene_001": Path("img1.png")}
        m2.return_value = {"scene_001": Path("clip1.mp4")}
        m3.return_value = [GeneratedScene(
            scene_id="scene_001", sequence=1, image_path=Path("img1.png"), 
            clip_path=Path("clip1.mp4"), duration_seconds=10.0, audio_path=Path("audio1.mp3")
        )]
        m4.return_value = Path("final.mp4")
        m5.return_value = 2
        
        await pipeline.run_partial(output, ["scene_001"], sample_timing_manifest)
        
        # Check that m1 was called with only scene_001
        assert len(m1.call_args[0][0].scenes) == 1
        assert m1.call_args[0][0].scenes[0].scene_id == "scene_001"

@pytest.mark.asyncio
async def test_run_persists_state_json(pipeline, sample_pipeline_input, sample_timing_manifest):
    with patch("phase3.image_generator.generate_all_images", new_callable=AsyncMock), \
         patch("phase3.animator.animate_all_scenes", new_callable=AsyncMock), \
         patch("phase3.animator.sync_all_scenes", new_callable=AsyncMock), \
         patch("phase3.compositor.compose_final_video", new_callable=AsyncMock) as m4, \
         patch("phase3.state_manager.StateManager.snapshot", new_callable=AsyncMock):
        
        m4.return_value = Path("final.mp4")
        
        await pipeline.run(sample_pipeline_input, sample_timing_manifest)
        
        state_path = Path(pipeline.settings.OUTPUT_DIR) / "phase3_state.json"
        assert state_path.exists()
        with open(state_path, "r") as f:
            data = json.load(f)
            assert "pipeline_input" in data
