from typing import Optional, Dict, Any
from supabase import Client


class UserRepository:
    def __init__(self, client: Client):
        self.client = client

    def get_persistent_login(self, token: str) -> Optional[Dict[str, Any]]:
        """Fetch a persistent login record by token."""
        try:
            response = (
                self.client.table("persistent_logins")
                .select("*")
                .eq("token", token)
                .single()
                .execute()
            )

            # supabase client can return error, mapping, sequence, or primitive
            if getattr(response, "error", None):
                raise RuntimeError(
                    f"Error fetching persistent login: {getattr(response, 'error', 'Unknown error')}"
                )

            data = getattr(response, "data", None)

            # already a mapping (single row)
            if isinstance(data, dict):
                return data

            # a sequence of rows
            if isinstance(data, (list, tuple)) and data:
                first = data[0]
                if isinstance(first, dict):
                    return first
                return None

            return None
        except Exception:
            raise RuntimeError("Error fetching persistent login")

    def create_persistent_login(
        self, user_id: str, token: str, expires_at: str
    ) -> None:
        """Create a new persistent login record."""
        try:
            self.client.table("persistent_logins").insert(
                {"user_id": user_id, "token": token, "expires_at": expires_at}
            ).execute()
        except Exception:
            raise RuntimeError("Error creating persistent login")

    def delete_persistent_login(self, token: str) -> None:
        """Delete a persistent login record by token."""
        try:
            self.client.table("persistent_logins").delete().eq("token", token).execute()
        except Exception:
            raise RuntimeError("Error deleting persistent login")
