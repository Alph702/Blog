from typing import Any, Dict, Optional
from repositories import UserRepository
import hashlib
import uuid
from datetime import datetime, timedelta
import pytz
import logging

logger = logging.getLogger("auth.service")


class AuthService:
    def __init__(self, user_repo: UserRepository):
        logger.debug("Initializing AuthService")
        self.repo = user_repo

    def authenticate(self, username: str, password: str) -> bool:
        """Simple authentication against predefined admin credentials."""
        try:
            from config import Config

            return (
                username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD
            )
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            raise Exception("Authentication error")

    def create_persistent_token(self, user_id: str) -> str:
        """Creates a persistent login token for the given user ID."""
        try:
            token: str = str(uuid.uuid4())
            hashed_token: str = hashlib.sha256(token.encode()).hexdigest()
            expires_at: str = (datetime.now(pytz.utc) + timedelta(days=30)).isoformat()

            self.repo.create_persistent_login(user_id, hashed_token, expires_at)
            return token
        except Exception as e:
            logger.error(f"Failed to create persistent token: {e}", exc_info=True)
            raise Exception("Token creation failed")

    def check_token(self, token: str) -> bool:
        """Checks if the provided token is valid and not expired."""
        if not token:
            return False

        try:
            hashed_token: str = hashlib.sha256(token.encode()).hexdigest()
            login: Optional[Dict[str, Any]] = self.repo.get_persistent_login(
                hashed_token
            )

            if not login:
                return False

            expires_at: datetime = datetime.fromisoformat(login["expires_at"])
            return expires_at > datetime.now(pytz.utc)
        except Exception as e:
            logger.error(f"Token validation failed: {e}", exc_info=True)
            raise Exception("Token validation error")

    def revoke_token(self, token: str) -> None:
        """Revokes the provided persistent login token."""
        if not token:
            return
        try:
            hashed_token: str = hashlib.sha256(token.encode()).hexdigest()
            self.repo.delete_persistent_login(hashed_token)
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}", exc_info=True)
            raise Exception("Token revocation failed")

    def __del__(self):
        logger.debug("Destroying AuthService instance")
