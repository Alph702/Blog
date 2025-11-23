from typing import Dict, Any, Optional
from supabase import Client


class VideoRepository:
    def __init__(self, client: Client):
        self.client = client

    def _extract_record(self, data: Any) -> Optional[Dict[str, Any]]:
        """Return the first record as a dict if possible, otherwise None."""
        if isinstance(data, dict):
            return data
        if isinstance(data, (list, tuple)) and data:
            first = data[0]
            if isinstance(first, dict):
                return first
        return None

    def get_by_id(self, video_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a video record by its ID."""
        try:
            response = (
                self.client.table("videos")
                .select("*")
                .eq("id", video_id)
                .single()
                .execute()
            )
            if getattr(response, "error", None):
                return None
            return self._extract_record(getattr(response, "data", None))
        except Exception:
            return None

    def create(
        self, filename: str, filepath: str, status: str = "processing"
    ) -> Dict[str, Any]:
        """Create a new video record."""
        payload = {"filename": filename, "filepath": filepath, "status": status}
        response = self.client.table("videos").insert(payload).execute()
        if getattr(response, "error", None):
            raise RuntimeError(
                f"Insert failed: {getattr(response, 'error', 'Unknown error')}"
            )
        record = self._extract_record(getattr(response, "data", None))
        if record is None:
            raise RuntimeError("Unexpected insert response shape")
        return record

    def update_status(self, video_id: int, status: str, filepath: str = ""):
        """Update the status (and optionally filepath) of a video record."""
        data = {"status": status}
        if filepath:
            data["filepath"] = filepath
        response = self.client.table("videos").update(data).eq("id", video_id).execute()
        if getattr(response, "error", None):
            raise RuntimeError(
                f"Update failed: {getattr(response, 'error', 'Unknown error')}"
            )
