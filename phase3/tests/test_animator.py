import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from phase3.animator import KenBurnsEffect, build_kenburns_filter, animate_scene_clip, AnimationError

def test_kenburns_from_mood_epic():
    assert KenBurnsEffect.from_mood("epic") == KenBurnsEffect.PAN_LEFT

def test_kenburns_from_mood_unknown_defaults():
    assert KenBurnsEffect.from_mood("unknown_mood") == KenBurnsEffect.ZOOM_IN

def test_build_kenburns_filter_contains_zoompan():
    for effect in KenBurnsEffect:
        filter_str = build_kenburns_filter(effect, 10.0, 1280, 720)
        assert "zoompan" in filter_str
        assert "1280x720" in filter_str

@pytest.mark.asyncio
async def test_animate_scene_clip_success(sample_scene, tmp_path):
    image_path = tmp_path / "scene_001.png"
    image_path.write_bytes(b"dummy")
    
    with patch("phase3.animator.asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc
        
        path = await animate_scene_clip(image_path, sample_scene, tmp_path)
        
        assert "scene_001_animated.mp4" in str(path)
        mock_exec.assert_called_once()

@pytest.mark.asyncio
async def test_animate_scene_clip_raises_on_ffmpeg_error(sample_scene, tmp_path):
    image_path = tmp_path / "scene_001.png"
    image_path.write_bytes(b"dummy")
    
    with patch("phase3.animator.asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"ffmpeg error")
        mock_proc.returncode = 1
        mock_exec.return_value = mock_proc
        
        with pytest.raises(AnimationError):
            await animate_scene_clip(image_path, sample_scene, tmp_path)
