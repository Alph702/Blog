from typing import Dict, Any, Optional
from supabase import Client
import logging

logger = logging.getLogger("video.repository")


class VideoRepository:
    def __init__(self, client: Client):
        logger.info("VideoRepository initialized")
        self.client = client

    def _extract_record(self, data: Any) -> Optional[Dict[str, Any]]:
        """Return the first record as a dict if possible, otherwise None."""
        logger.debug(f"_extract_record() called with data type: {type(data).__name__}")
        try:
            if isinstance(data, dict):
                logger.debug("Data is dict, returning as record")
                return data
            if isinstance(data, (list, tuple)) and data:
                logger.debug(
                    f"Data is sequence with {len(data)} items, extracting first"
                )
                first = data[0]
                if isinstance(first, dict):
                    return first
            logger.debug("Data is empty or unrecognized")
            return None
        except Exception:
            logger.exception("Error extracting record")
            raise RuntimeError("Failed to extract record from response data")

    def get_by_id(self, video_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a video record by its ID."""
        logger.debug(f"get_by_id() called with video_id: {video_id}")
        try:
            logger.debug("Querying videos table for single record")
            response = (
                self.client.table("videos")
                .select("*")
                .eq("id", video_id)
                .single()
                .execute()
            )
            logger.debug(
                f"Query executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.error(
                    f"Error fetching video by ID {video_id}: {getattr(response, 'error')}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Query failed: {getattr(response, 'error', 'Unknown error')}"
                )
            logger.debug("Extracting record from response")
            return self._extract_record(getattr(response, "data", None))
        except Exception:
            logger.exception(
                f"Exception occurred while fetching video by ID {video_id}"
            )
            raise RuntimeError("Failed to fetch video by ID")

    def create(
        self, filename: str, filepath: str, status: str = "processing"
    ) -> Dict[str, Any]:
        """Create a new video record."""
        logger.debug(f"create() called with filename: {filename}, status: {status}")
        try:
            logger.debug("Preparing payload and inserting record")
            payload = {"filename": filename, "filepath": filepath, "status": status}
            response = self.client.table("videos").insert(payload).execute()
            logger.debug(
                f"Insert executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.error(
                    f"Insert failed with error: {getattr(response, 'error', 'Unknown error')}"
                )
                raise RuntimeError(
                    f"Insert failed: {getattr(response, 'error', 'Unknown error')}"
                )
            logger.debug("Extracting inserted record from response")
            record = self._extract_record(getattr(response, "data", None))
            if record is None:
                logger.error("Unexpected insert response shape - no record returned")
                raise RuntimeError("Unexpected insert response shape")
            return record
        except Exception as e:
            logger.exception("Exception occurred while creating video record")
            raise RuntimeError("Failed to create video record") from e

    def update_status(self, video_id: int, status: str, filepath: str = ""):
        """Update the status (and optionally filepath) of a video record."""
        logger.debug(
            f"update_status() called for video_id: {video_id}, status: {status}"
        )
        try:
            data = {"status": status}
            if filepath:
                logger.debug("Updating filepath as well")
                data["filepath"] = filepath
            logger.debug(f"Updating video record with data: {data}")
            response = (
                self.client.table("videos").update(data).eq("id", video_id).execute()
            )
            logger.debug(
                f"Update executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.error(
                    f"Error updating video ID {video_id}: {getattr(response, 'error')}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Update failed: {getattr(response, 'error', 'Unknown error')}"
                )
        except Exception as e:
            logger.exception(f"Exception occurred while updating video ID {video_id}")
            raise RuntimeError("Failed to update video record") from e

    def __del__(self):
        logger.info("VideoRepository instance is being destroyed")
