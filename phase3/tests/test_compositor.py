import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from phase3.compositor import build_concat_filter, concatenate_scenes, mix_background_music, compose_final_video, GeneratedScene

@pytest.fixture
def mock_generated_scenes(tmp_path):
    return [
        GeneratedScene(
            scene_id="scene_001",
            sequence=1,
            image_path=tmp_path / "img1.png",
            clip_path=tmp_path / "clip1.mp4",
            duration_seconds=10.0,
            audio_path=tmp_path / "audio1.mp3"
        ),
        GeneratedScene(
            scene_id="scene_002",
            sequence=2,
            image_path=tmp_path / "img2.png",
            clip_path=tmp_path / "clip2.mp4",
            duration_seconds=10.0,
            audio_path=tmp_path / "audio2.mp3"
        )
    ]

def test_build_concat_filter_two_scenes(mock_generated_scenes):
    filter_str, label = build_concat_filter(mock_generated_scenes, transition_duration=0.5)
    assert "xfade" in filter_str
    assert "offset=9.500" in filter_str
    assert label == "v01"

def test_build_concat_filter_single_scene(mock_generated_scenes):
    filter_str, label = build_concat_filter(mock_generated_scenes[:1])
    assert "xfade" not in filter_str
    assert "copy" in filter_str
    assert label == "[vout]"

@pytest.mark.asyncio
async def test_compose_final_video_calls_concat_and_bgm(mock_generated_scenes, sample_timing_manifest, tmp_path):
    with patch("phase3.compositor.concatenate_scenes", new_callable=AsyncMock) as mock_concat, \
         patch("phase3.compositor.mix_background_music", new_callable=AsyncMock) as mock_bgm:
        
        mock_concat.return_value = tmp_path / "concat.mp4"
        mock_bgm.return_value = tmp_path / "final.mp4"
        
        await compose_final_video(mock_generated_scenes, sample_timing_manifest, tmp_path)
        
        mock_concat.assert_called_once()
        mock_bgm.assert_called_once()

@pytest.mark.asyncio
async def test_compose_final_video_skips_bgm_when_none(mock_generated_scenes, sample_timing_manifest, tmp_path):
    sample_timing_manifest.background_music = None
    
    with patch("phase3.compositor.concatenate_scenes", new_callable=AsyncMock) as mock_concat, \
         patch("phase3.compositor.mix_background_music", new_callable=AsyncMock) as mock_bgm, \
         patch("shutil.copy", MagicMock()) as mock_copy:
        
        mock_concat.return_value = tmp_path / "concat.mp4"
        
        await compose_final_video(mock_generated_scenes, sample_timing_manifest, tmp_path)
        
        mock_concat.assert_called_once()
        mock_bgm.assert_not_called()
        mock_copy.assert_called_once()
