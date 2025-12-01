from .auth import auth_bp
from .blog import blog_bp
from .admin import admin_bp
from .api import api_bp
import logging

logger = logging.getLogger(__name__)
logger.debug("Blueprints package imported")

__all__ = ["auth_bp", "blog_bp", "admin_bp", "api_bp"]
