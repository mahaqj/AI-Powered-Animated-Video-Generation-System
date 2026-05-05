import pytest
import httpx
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from phase3.image_generator import build_image_prompt, generate_scene_image, generate_all_images, ImageGenerationError

def test_build_image_prompt_contains_mood_style(sample_scene, sample_character):
    prompt = build_image_prompt(sample_scene, [sample_character])
    assert "epic cinematic" in prompt.lower()
    assert "golden hour" in prompt.lower()
    assert "Aria" not in prompt # character name shouldn't be in prompt, only description
    assert "silver hair" in prompt

def test_build_image_prompt_max_length(sample_scene, sample_character):
    sample_scene.visual_prompt = "A " * 500 # use spaces to test word-break truncation
    prompt = build_image_prompt(sample_scene, [sample_character])
    assert len(prompt) <= 400
    # The prompt might end with "highly detailed, 4k, sharp focus" or part of it
    # Just check it's truncated correctly
    assert len(prompt) > 0

@pytest.mark.asyncio
async def test_generate_scene_image_success(sample_scene, sample_character, tmp_path):
    mock_response = MagicMock()
    mock_response.content = b"\x89PNG\r\n"
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with patch("aiofiles.open", MagicMock()) as mock_open:
            # We need to mock the context manager returned by aiofiles.open
            mock_f = AsyncMock()
            mock_open.return_value.__aenter__.return_value = mock_f
            
            path = await generate_scene_image(sample_scene, [sample_character], tmp_path)
            
            assert path.name == "scene_001.png"
            mock_f.write.assert_called_once_with(b"\x89PNG\r\n")

@pytest.mark.asyncio
async def test_generate_scene_image_raises_on_http_error(sample_scene, sample_character, tmp_path):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())
        
        with pytest.raises(ImageGenerationError):
            await generate_scene_image(sample_scene, [sample_character], tmp_path)

@pytest.mark.asyncio
async def test_generate_all_images_returns_dict_keyed_by_scene_id(sample_pipeline_input, tmp_path):
    with patch("phase3.image_generator.generate_scene_image", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = tmp_path / "mock.png"
        
        result = await generate_all_images(sample_pipeline_input, tmp_path)
        
        assert len(result) == 2
        assert "scene_001" in result
        assert "scene_002" in result
        assert mock_gen.call_count == 2
