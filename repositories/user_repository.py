from typing import Optional, Dict, Any
from supabase import Client
import logging

logger = logging.getLogger("auth.repository")


class UserRepository:
    def __init__(self, client: Client):
        logger.debug("Initializing UserRepository with Supabase client")
        self.client = client

    def get_persistent_login(self, token: str) -> Optional[Dict[str, Any]]:
        """Fetch a persistent login record by token."""
        logger.debug(f"get_persistent_login() called with token: {token[:20]}...")
        try:
            logger.debug("Querying persistent_logins table")
            response = (
                self.client.table("persistent_logins")
                .select("*")
                .eq("token", token)
                .single()
                .execute()
            )

            # supabase client can return error, mapping, sequence, or primitive
            logger.debug(
                f"Query executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.error(
                    f"Error fetching persistent login: {getattr(response, 'error', 'Unknown error')}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Error fetching persistent login: {getattr(response, 'error', 'Unknown error')}"
                )

            data = getattr(response, "data", None)
            logger.debug("Extracting record from response")

            # already a mapping (single row)
            if isinstance(data, dict):
                logger.debug("Response data is dict")
                return data

            # a sequence of rows
            if isinstance(data, (list, tuple)) and data:
                logger.debug(f"Response data is sequence with {len(data)} items")
                first = data[0]
                if isinstance(first, dict):
                    return first
                return None

            logger.debug("Response data is empty")
            return None
        except Exception:
            logger.exception("Exception occurred while fetching persistent login")
            raise RuntimeError("Error fetching persistent login")

    def create_persistent_login(
        self, user_id: str, token: str, expires_at: str
    ) -> None:
        """Create a new persistent login record."""
        logger.debug(f"create_persistent_login() called for user_id: {user_id}")
        try:
            logger.debug("Inserting persistent login record")
            self.client.table("persistent_logins").insert(
                {"user_id": user_id, "token": token, "expires_at": expires_at}
            ).execute()
            logger.debug("Persistent login record inserted successfully")
        except Exception:
            logger.error(
                "Error occurred while creating persistent login", exc_info=True
            )
            raise RuntimeError("Error creating persistent login")

    def delete_persistent_login(self, token: str) -> None:
        """Delete a persistent login record by token."""
        logger.debug(f"delete_persistent_login() called with token: {token[:20]}...")
        try:
            logger.debug("Deleting persistent login record")
            self.client.table("persistent_logins").delete().eq("token", token).execute()
            logger.debug("Persistent login record deleted successfully")
        except Exception:
            logger.error(
                "Error occurred while deleting persistent login", exc_info=True
            )
            raise RuntimeError("Error deleting persistent login")

    def __del__(self):
        logger.debug("UserRepository instance is being destroyed")
