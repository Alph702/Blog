from typing import List, Dict, Optional, Any
from supabase import Client


class PostRepository:
    def __init__(self, client: Client):
        self.client = client

    def _extract_records(self, data: Any) -> List[Dict[str, Any]]:
        """Normalize response.data into a list of dict records."""
        if isinstance(data, dict):
            return [data]
        if isinstance(data, (list, tuple)):
            return [item for item in data if isinstance(item, dict)]
        return []

    def get_all(
        self, limit: int = 10, offset: int = 0, order_by: str = "id"
    ) -> List[Dict[str, Any]]:
        """Fetch all posts with pagination and ordering."""
        try:
            response = (
                self.client.table("posts")
                .select("*")
                .order(order_by, desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            if getattr(response, "error", None):
                return []
            data = getattr(response, "data", None)
            return self._extract_records(data)
        except Exception as e:
            raise RuntimeError(f"Error fetching posts: {e}")

    def get_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a post by its ID."""
        try:
            response = (
                self.client.table("posts")
                .select("*")
                .eq("id", post_id)
                .single()
                .execute()
            )
            if getattr(response, "error", None):
                return None
            data = getattr(response, "data", None)
            records = self._extract_records(data)
            return records[0] if records else None
        except Exception:
            return None

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new post."""
        try:
            response = self.client.table("posts").insert(data).execute()
            if getattr(response, "error", None):
                raise RuntimeError(
                    f"Error creating post: {getattr(response, 'error', 'Unknown error')}"
                )
            records = self._extract_records(getattr(response, "data", None))
            return records[0] if records else None
        except Exception as e:
            raise RuntimeError(f"Error creating post: {e}")

    def update(self, post_id: int, data: Dict[str, Any]):
        """Update an existing post."""
        try:
            self.client.table("posts").update(data).eq("id", post_id).execute()
        except Exception as e:
            raise RuntimeError(f"Error updating post: {e}")

    def delete(self, post_id: int):
        """Delete a post by its ID."""
        try:
            self.client.table("posts").delete().eq("id", post_id).execute()
        except Exception as e:
            raise RuntimeError(f"Error deleting post: {e}")
