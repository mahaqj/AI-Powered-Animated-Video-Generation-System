import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import shutil

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    OUTPUT_DIR: str = "outputs/6MAY-352AM-RUN"
    POLLINATIONS_IMAGE_URL: str = "https://image.pollinations.ai/prompt/"
    POLLINATIONS_MODEL: str = "flux"
    IMAGE_WIDTH: int = 1024
    IMAGE_HEIGHT: int = 1024
    VIDEO_FPS: int = 24
    FFMPEG_PATH: str = "ffmpeg"
    LOG_LEVEL: str = "INFO"
    STATE_DB_PATH: str = "outputs/phase3_versions.db"

    def model_post_init(self, __context):
        # Auto-detect ffmpeg if default is not found
        if not shutil.which(self.FFMPEG_PATH):
            try:
                import imageio_ffmpeg
                self.FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                pass

        output_path = Path(self.OUTPUT_DIR)
        (output_path / "images").mkdir(parents=True, exist_ok=True)
        (output_path / "clips").mkdir(parents=True, exist_ok=True)
        (output_path / "final").mkdir(parents=True, exist_ok=True)
        
        # Also ensure state DB parent dir exists
        Path(self.STATE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

@lru_cache()
def get_settings():
    return Settings()
