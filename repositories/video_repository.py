from typing import Dict, Any, Optional
from supabase import Client
import logging

logger = logging.getLogger('video.repository')

class VideoRepository:
    def __init__(self, client: Client):
        logger.info("VideoRepository initialized")
        self.client = client

    def _extract_record(self, data: Any) -> Optional[Dict[str, Any]]:
        """Return the first record as a dict if possible, otherwise None."""
        try:
            if isinstance(data, dict):
                return data
            if isinstance(data, (list, tuple)) and data:
                first = data[0]
                if isinstance(first, dict):
                    return first
            return None
        except Exception:
            logger.exception("Error extracting record")
            raise RuntimeError("Failed to extract record from response data")

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
                logger.error(f"Error fetching video by ID {video_id}: {getattr(response, 'error')}")
                raise RuntimeError(f"Query failed: {getattr(response, 'error', 'Unknown error')}")
            return self._extract_record(getattr(response, "data", None))
        except Exception:
            logger.exception(f"Exception occurred while fetching video by ID {video_id}")
            raise RuntimeError("Failed to fetch video by ID")

    def create(
        self, filename: str, filepath: str, status: str = "processing"
    ) -> Dict[str, Any]:
        """Create a new video record."""
        try:
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
        except Exception as e:
            logger.exception("Exception occurred while creating video record")
            raise RuntimeError("Failed to create video record") from e

    def update_status(self, video_id: int, status: str, filepath: str = ""):
        """Update the status (and optionally filepath) of a video record."""
        try:
            data = {"status": status}
            if filepath:
                data["filepath"] = filepath
            response = self.client.table("videos").update(data).eq("id", video_id).execute()
            if getattr(response, "error", None):
                logger.error(f"Error updating video ID {video_id}: {getattr(response, 'error')}")
                raise RuntimeError(
                    f"Update failed: {getattr(response, 'error', 'Unknown error')}"
                )
        except Exception as e:
            logger.exception(f"Exception occurred while updating video ID {video_id}")
            raise RuntimeError("Failed to update video record") from e
    
    def __del__(self):
        logger.info("VideoRepository instance is being destroyed")
