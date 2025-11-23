from typing import List, Dict, Optional, Any
from supabase import Client
from container import Config
from werkzeug.datastructures import FileStorage


class PostRepository:
    def __init__(self, client: Client):
        self.client: Client = client

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

    def filter_by_date(
        self,
        year: str,
        month: str,
        day: str,
        limit: int = 10,
        offset: int = 0,
        order_by: str = "id",
    ) -> List[Dict[str, Any]]:
        posts: List[Dict[str, Any]] = []
        try:
            query = (
                self.client.table("posts")
                .select("*")
                .order(order_by, desc=True)
                .limit(limit)
                .offset(offset)
            )

            if year != "any":
                query = query.eq("year", year)
            if month != "any":
                query = query.eq("month", month)
            if day != "any":
                query = query.eq("day", day)

            response = query.execute()
            if getattr(response, "error", None):
                return []

            data = getattr(response, "data", None)
            posts = self._extract_records(data)
            return posts
        except Exception as e:
            raise RuntimeError(f"Error filtering posts: {e}")

    def upload_file(self, file: FileStorage, file_name: str) -> Optional[str]:
        """Upload a file to Supabase storage and return its public URL."""
        try:
            file_bytes = file.read()
        except Exception as e:
            file_bytes = None
            raise RuntimeError(f"Failed to read uploaded file into memory: {e}")

        if file_bytes:
            image_url: Optional[str] = None
            try:
                try:
                    self.client.storage.from_(Config.BLOG_IMAGES_BUCKET).upload(
                        file_name, file_bytes, {"content-type": file.content_type}
                    )
                    image_url = f"{Config.SUPABASE_URL}/storage/v1/object/public/{Config.BLOG_IMAGES_BUCKET}/{file_name}"
                except Exception as e:
                    if getattr(e, "status", "unknown") == 409:
                        image_url = f"{Config.SUPABASE_URL}/storage/v1/object/public/{Config.BLOG_IMAGES_BUCKET}/{file_name}"
                    else:
                        image_url = None
                        raise RuntimeError(
                            f"Failed to upload file to Supabase storage: {e} with status {getattr(e, 'status', 'unknown')}"
                        )
            except Exception as e:
                image_url = None
                raise RuntimeError(f"Failed to upload file to Supabase storage: {e}")
            return image_url
        return None

    def has_next_page(self, page: int) -> bool:
        """Check if there is a next page of posts."""
        try:
            offset = page * Config.POSTS_PER_PAGE
            response = (
                self.client.table("posts")
                .select("id")
                .offset(offset)
                .limit(1)
                .execute()
            )
            if getattr(response, "error", None):
                return False
            data = getattr(response, "data", None)
            records = self._extract_records(data)
            count = len(records)
            return True if count > 0 else False
        except Exception:
            return False
