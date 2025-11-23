from typing import Any, Dict, Optional
from werkzeug.datastructures import FileStorage
from repositories import VideoRepository
from services.worker_service import WorkerService


class VideoService:
    """Service for handling video-related operations."""

    def __init__(self, video_repo: VideoRepository, worker_service: WorkerService):
        self.repo = video_repo
        self.worker = worker_service

    def upload_video(self, file: FileStorage) -> Optional[int]:
        """Uploads a video file and queues it for processing."""
        file_id: Optional[int] = self.worker.queue_file(file)

        return file_id

    def get_video_by_id(self, video_id: int) -> Optional[dict]:
        """Fetches video metadata by its ID."""
        video_record: Optional[Dict[str, Any]] = self.repo.get_by_id(video_id)

        return video_record
