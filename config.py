import os
from dotenv import load_dotenv


class Config:
    """Configuration class to manage environment variables."""

    load_dotenv()
    SECRET_KEY: str = os.getenv("SECRET_KEY", "UNDEFINED")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "UNDEFINED")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY" or "SUPABASE_ANON_KEY", "UNDEFINED")
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
