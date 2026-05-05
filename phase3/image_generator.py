import httpx
import asyncio
import logging
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional
import aiofiles

from .schemas import SceneDef, CharacterDef, PipelineInput
from .config import get_settings

settings = get_settings()
logger = logging.getLogger("phase3.image_generator")

class ImageGenerationError(Exception):
    """Custom exception for all image generation failures"""
    pass

MOOD_STYLE_MAP: Dict[str, str] = {
    "happy":       "warm golden lighting, vibrant colors, cheerful atmosphere, photorealistic",
    "sad":         "muted desaturated tones, soft overcast light, melancholic atmosphere",
    "dark":        "dark dramatic lighting, deep shadows, cinematic noir, high contrast",
    "epic":        "dramatic wide angle lens, golden hour light, epic cinematic scale",
    "mysterious":  "foggy atmosphere, cool blue tones, mysterious diffused shadows",
    "neutral":     "natural soft lighting, balanced composition, photorealistic",
    "angry":       "harsh red-orange lighting, high contrast, intense atmosphere",
    "romantic":    "warm pink-gold bokeh, soft focus, dreamy atmosphere",
}

DEFAULT_STYLE = "natural lighting, cinematic composition, photorealistic"

def build_image_prompt(scene: SceneDef, characters: List[CharacterDef]) -> str:
    """Start with scene.visual_prompt, add character descriptions and mood style."""
    prompt = scene.visual_prompt
    
    # Find characters mentioned in scene dialogue
    mentioned_ids = {d.character_id for d in scene.dialogue}
    for char_id in mentioned_ids:
        char = next((c for c in characters if c.id == char_id), None)
        if char:
            prompt += f", {char.visual_description}"
            
    # Append mood style
    style = MOOD_STYLE_MAP.get(scene.mood.lower(), DEFAULT_STYLE)
    prompt += f", {style}"
    
    # Append global quality tokens
    prompt += ", highly detailed, 4k, sharp focus"
    
    # Truncate to 400 characters, breaking at last space
    if len(prompt) > 400:
        truncated = prompt[:400]
        last_space = truncated.rfind(" ")
        if last_space != -1:
            prompt = truncated[:last_space]
        else:
            prompt = truncated
            
    return prompt

async def generate_scene_image(scene: SceneDef, characters: List[CharacterDef], output_dir: Path, seed: int | None = None, retries: int = 5) -> Path:
    """Enrich prompt and download image from Pollinations.ai with retry logic."""
    prompt = build_image_prompt(scene, characters)
    encoded_prompt = urllib.parse.quote(prompt, safe="")
    
    url = f"{settings.POLLINATIONS_IMAGE_URL}/{encoded_prompt}"
    params = {
        "width": settings.IMAGE_WIDTH,
        "height": settings.IMAGE_HEIGHT,
        "model": settings.POLLINATIONS_MODEL,
        "nologo": "true"
    }
    if seed is not None:
        params["seed"] = seed
        
    last_error = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 429:
                    raise httpx.HTTPStatusError("Rate limit", request=response.request, response=response)
                
                response.raise_for_status()
                
                output_path = output_dir / f"{scene.scene_id}.png"
                async with aiofiles.open(output_path, "wb") as f:
                    await f.write(response.content)
                    
                logger.info(f"[ImageGen] Scene {scene.scene_id} saved to {output_path} (Attempt {attempt+1})")
                return output_path
                
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            last_error = e
            status_code = getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0
            if status_code == 429 or isinstance(e, httpx.RequestError):
                wait_time = (attempt + 1) * 10 # More aggressive backoff: 10, 20, 30, 40, 50s
                logger.warning(f"[ImageGen] Rate limited or connection issue for scene {scene.scene_id}. Retrying in {wait_time}s... ({e})")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[ImageGen Error] HTTP error {status_code} for scene {scene.scene_id}")
                break 
        except Exception as e:
            last_error = e
            logger.error(f"[ImageGen Error] Unexpected error for scene {scene.scene_id}: {e}")
            await asyncio.sleep(5)
            
    raise ImageGenerationError(f"Failed to generate image for {scene.scene_id} after {retries} attempts. Last error: {last_error}")

async def generate_all_images(pipeline_input: PipelineInput, output_dir: Path, seed: int | None = None) -> Dict[str, Path]:
    """Generate all scene images sequentially with a delay to respect rate limits."""
    logger.info(f"[ImageGen] Generating {len(pipeline_input.scenes)} scene images sequentially")
    
    results = {}
    for i, scene in enumerate(pipeline_input.scenes):
        if i > 0:
            logger.info(f"[ImageGen] Waiting 3s before next scene...")
            await asyncio.sleep(3.0)
        
        path = await generate_scene_image(scene, pipeline_input.characters, output_dir, seed)
        results[scene.scene_id] = path
        
    return results
