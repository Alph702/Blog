import os
from dotenv import load_dotenv
import logging

# Module logger
logger = logging.getLogger(__name__)


class Config:
    """Configuration class to manage environment variables."""

    logger.debug("Loading environment variables from .env file")
    load_dotenv()

    logger.debug("Initializing configuration")
    SECRET_KEY: str = os.getenv("SECRET_KEY") or os.urandom(24).hex()
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "UNDEFINED")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") or os.getenv(
        "SUPABASE_ANON_KEY", "UNDEFINED"
    )
    BLOG_IMAGES_BUCKET: str = os.getenv("BLOG_IMAGES_BUCKET", "UNDEFINED")
    BLOG_VIDEOS_BUCKET: str = os.getenv("BLOG_VIDEOS_BUCKET", "UNDEFINED")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "UNDEFINED")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "UNDEFINED")
    POSTS_PER_PAGE: int = 10
    ALLOWED_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "bmp",
        "webp",
        "mp4",
        "mov",
        "avi",
        "mkv",
        "webm",
    }

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")

    @property
    def LOGGING_LEVEL(self) -> int:
        """Converts the LOG_LEVEL string to a logging module constant."""
        return getattr(logging, self.LOG_LEVEL, logging.INFO)
