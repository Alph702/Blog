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
        logger.debug(f"authenticate() called with username: {username}")
        try:
            from config import Config

            logger.debug("Comparing username and password with config")
            result = (
                username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD
            )
            logger.debug(f"Authentication result: {result}")
            return result
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            raise Exception("Authentication error")

    def create_persistent_token(self, user_id: str) -> str:
        """Creates a persistent login token for the given user ID."""
        logger.debug(f"create_persistent_token() called for user_id: {user_id}")
        try:
            logger.debug("Generating UUID for token")
            token: str = str(uuid.uuid4())
            logger.debug("Hashing token with SHA256")
            hashed_token: str = hashlib.sha256(token.encode()).hexdigest()
            logger.debug("Calculating expiration date (30 days from now)")
            expires_at: str = (datetime.now(pytz.utc) + timedelta(days=30)).isoformat()

            logger.debug(f"Calling repo.create_persistent_login for user_id: {user_id}")
            self.repo.create_persistent_login(user_id, hashed_token, expires_at)
            logger.debug("Token created successfully")
            return token
        except Exception as e:
            logger.error(f"Failed to create persistent token: {e}", exc_info=True)
            raise Exception("Token creation failed")

    def check_token(self, token: str) -> bool:
        """Checks if the provided token is valid and not expired."""
        logger.debug("check_token() called")
        if not token:
            logger.debug("Token is empty, returning False")
            return False

        try:
            logger.debug("Hashing token with SHA256")
            hashed_token: str = hashlib.sha256(token.encode()).hexdigest()
            logger.debug("Calling repo.get_persistent_login")
            login: Optional[Dict[str, Any]] = self.repo.get_persistent_login(
                hashed_token
            )

            if not login:
                logger.debug("No login record found for token")
                return False

            logger.debug("Parsing expiration date")
            expires_at: datetime = datetime.fromisoformat(login["expires_at"])
            logger.debug("Checking if token is expired")
            is_valid = expires_at > datetime.now(pytz.utc)
            logger.debug(f"Token valid: {is_valid}")
            return is_valid
        except Exception as e:
            logger.error(f"Token validation failed: {e}", exc_info=True)
            raise Exception("Token validation error")

    def revoke_token(self, token: str) -> None:
        """Revokes the provided persistent login token."""
        logger.debug("revoke_token() called")
        if not token:
            logger.debug("Token is empty, returning early")
            return
        try:
            logger.debug("Hashing token with SHA256")
            hashed_token: str = hashlib.sha256(token.encode()).hexdigest()
            logger.debug("Calling repo.delete_persistent_login")
            self.repo.delete_persistent_login(hashed_token)
            logger.debug("Token revoked successfully")
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}", exc_info=True)
            raise Exception("Token revocation failed")

    def __del__(self):
        logger.debug("Destroying AuthService instance")
