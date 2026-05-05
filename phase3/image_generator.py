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

# User's "Secret Sauce" Style Prefix
STYLE_PREFIX = "3D animated character portrait, pixar style, high quality, vibrant colors, stylized character, unreal engine 5, "

MOOD_STYLE_MAP: Dict[str, str] = {
    "happy":       "warm golden lighting, cheerful atmosphere",
    "sad":         "muted desaturated tones, melancholic atmosphere",
    "dark":        "dark dramatic lighting, deep shadows, cinematic noir",
    "epic":        "dramatic wide angle lens, epic cinematic scale",
    "mysterious":  "foggy atmosphere, mysterious diffused shadows",
    "neutral":     "natural soft lighting, balanced composition",
    "angry":       "harsh red-orange lighting, intense atmosphere",
    "romantic":    "warm pink-gold bokeh, dreamy atmosphere",
}

DEFAULT_STYLE = "natural lighting, cinematic composition"

def build_image_prompt(scene: SceneDef, characters: List[CharacterDef]) -> str:
    """Start with STYLE_PREFIX, then scene.visual_prompt, then character descriptions and mood style."""
    prompt = STYLE_PREFIX
    prompt += scene.visual_prompt
    
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
    prompt += ", highly detailed, sharp focus"
    
    # Truncate to 1000 characters (Pollinations handles long prompts well)
    return prompt[:1000]

async def generate_scene_image(scene: SceneDef, characters: List[CharacterDef], output_dir: Path, seed: int | None = None, retries: int = 5) -> Path:
    """Enrich prompt and download image from Pollinations.ai with retry logic."""
    prompt = build_image_prompt(scene, characters)
    encoded_prompt = urllib.parse.quote(prompt, safe="")
    
    # User's requested URL structure
    url = f"{settings.POLLINATIONS_IMAGE_URL}{encoded_prompt}"
    params = {
        "nologo": "true",
        "private": "true"
    }
    # Optional width/height if set in settings, but defaults to square if not provided
    if settings.IMAGE_WIDTH and settings.IMAGE_HEIGHT:
        params["width"] = settings.IMAGE_WIDTH
        params["height"] = settings.IMAGE_HEIGHT
        
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
                wait_time = (attempt + 1) * 10
                logger.warning(f"[ImageGen] Issue for scene {scene.scene_id}. Retrying in {wait_time}s... ({e})")
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
