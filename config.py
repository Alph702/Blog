import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class to manage environment variables."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_key")
    SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")
    BLOG_IMAGES_BUCKET: str = os.getenv("BLOG_IMAGES_BUCKET", "blog_images")
    BLOG_VIDEOS_BUCKET: str = os.getenv("BLOG_VIDEOS_BUCKET", "blog_videos")
    ADMIN_USERNAME: str | None = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD: str | None = os.getenv("ADMIN_PASSWORD")
    POSTS_PER_PAGE: int = 10
