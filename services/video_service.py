from typing import Any, Dict, Optional
from werkzeug.datastructures import FileStorage
from repositories import VideoRepository
from services.worker_service import WorkerService
import logging

logger = logging.getLogger("video.service")


class VideoService:
    """Service for handling video-related operations."""

    def __init__(self, video_repo: VideoRepository, worker_service: WorkerService):
        logger.debug("Initializing VideoService")
        self.repo = video_repo
        self.worker = worker_service

    def upload_video(self, file: FileStorage) -> Optional[int]:
        """Uploads a video file and queues it for processing."""
        logger.debug(f"upload_video() called with filename: {file.filename}")
        try:
            logger.debug("Calling worker.queue_file()")
            file_id: Optional[int] = self.worker.queue_file(file)
            logger.debug(f"Video queued with file_id: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Failed to queue video file: {e}", exc_info=True)
            raise Exception("Video upload failed")

    def get_video_by_id(self, video_id: int) -> Optional[dict]:
        """Fetches video metadata by its ID."""
        logger.debug(f"get_video_by_id() called with video_id: {video_id}")
        try:
            logger.debug("Calling repo.get_by_id()")
            video_record: Optional[Dict[str, Any]] = self.repo.get_by_id(video_id)
            logger.debug(f"Retrieved video record: {bool(video_record)}")
            return video_record
        except Exception as e:
            logger.error(
                f"Failed to fetch video with ID {video_id}: {e}", exc_info=True
            )
            raise Exception("Video retrieval failed")

    def __del__(self):
        logger.debug("Destroying VideoService instance")
