from typing import List, Dict, Any, Optional
from repositories import PostRepository
from services import VideoService
from dateutil import parser


class PostService:
    def __init__(self, repo: PostRepository, video_service: VideoService):
        self.repo: PostRepository = repo
        self.video_service: VideoService = video_service

    def get_recent_posts(self, page: int = 1) -> List[Dict[str, Any]]:
        limit: int = 10
        offset: int = (page - 1) * limit

        posts: List[Dict[str, Any]] = self.repo.get_all(
            limit=limit, offset=offset, order_by="timestamp" or "id"
        )

        for post in posts:
            post["formatted_timestamp"] = self._format_date(post.get("timestamp"))
            if post.get("video_id"):
                post["video"] = self.video_service.get_video_by_id(post["video_id"])

        return posts

    def get_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        return self.repo.get_by_id(post_id)

    def create_post(
        self,
        title: Optional[str],
        content: str,
        image_url: Optional[str] = None,
        video_id: Optional[int] = None,
    ):
        data = {
            "title": title,
            "content": content,
            "image": image_url,
            "video_id": video_id,
            "timestamp": self._get_current_timestamp(),
        }
        return self.repo.create(data)

    # TODO: Implement update_post method
    def update_post(self, post_id: int, form_data, files):
        # Business logic for updating
        pass

    def delete_post(self, post_id: int):
        self.repo.delete(post_id)

    def _format_date(self, date_str: Optional[str]) -> str:
        if not date_str:
            return ""
        try:
            dt = parser.parse(date_str).replace(tzinfo=None)
            return dt.strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            return str(date_str)

    def _get_current_timestamp(self) -> str:
        from datetime import datetime
        import pytz

        # TODO: Get user timezone
        local_tz = pytz.timezone("Asia/Karachi")
        return datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")
