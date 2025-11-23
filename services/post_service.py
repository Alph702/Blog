from typing import List, Dict, Any, Optional, cast
from repositories import PostRepository
from services import VideoService
from dateutil import parser
from config import Config
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class PostService:
    def __init__(self, repo: PostRepository, video_service: VideoService):
        self.repo: PostRepository = repo
        self.video_service: VideoService = video_service
        self.config: Config = Config()
        self.limit: int = self.config.POSTS_PER_PAGE

    def get_recent_posts(self, page: int = 1) -> List[Dict[str, Any]]:
        offset: int = (page - 1) * self.limit

        posts: List[Dict[str, Any]] = self.repo.get_all(
            limit=self.limit, offset=offset, order_by="timestamp" or "id"
        )

        for post in posts:
            post["formatted_timestamp"] = self._format_date(
                cast(int, post.get("year")),
                cast(int, post.get("month")),
                cast(int, post.get("day")),
                cast(str, post.get("time")),
            )
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
        timestamp: Dict[str, str] = self._get_current_timestamp()
        data = {
            "title": title,
            "content": content,
            "image": image_url,
            "video_id": video_id,
            "year": timestamp["Year"],
            "month": timestamp["Month"],
            "day": timestamp["Day"],
            "time": timestamp["Time"],
        }
        return self.repo.create(data)

    # TODO: Implement update_post method
    def update_post(self, post_id: int, form_data, files):
        # Business logic for updating
        pass

    def filter_posts(
        self, year: str, month: str, day: str, page: int = 1
    ) -> List[Dict[str, Any]]:
        posts: List[Dict[str, Any]] = self.repo.filter_by_date(
            year,
            month,
            day,
            limit=self.limit,
            offset=(page - 1) * self.limit,
            order_by="id",
        )

        for post in posts:
            post["formatted_timestamp"] = self._format_date(
                cast(int, post.get("year")),
                cast(int, post.get("month")),
                cast(int, post.get("day")),
                cast(str, post.get("time")),
            )
            if post.get("video_id"):
                post["video"] = self.video_service.get_video_by_id(post["video_id"])

        return posts

    def delete_post(self, post_id: int):
        self.repo.delete(post_id)

    def upload_image(self, file: FileStorage) -> Optional[str]:
        if file and self._allowed_file(str(file.filename)):
            filename = secure_filename(str(file.filename))

            image_url: Optional[str] = self.repo.upload_file(file, filename)
            return image_url
        else:
            return None

    def has_next_page(self, page: int) -> bool:
        return self.repo.has_next_page(page)

    def _format_date(self, year: int, month: int, day: int, time: str) -> str:
        if not year or not month or not day or not time:
            return ""
        try:
            dt = parser.parse(f"{year}-{month}-{day} {time}").replace(tzinfo=None)
            return dt.strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            return str(f"{year}-{month}-{day} {time}")

    def _get_current_timestamp(self) -> Dict[str, str]:
        from datetime import datetime
        import pytz

        # TODO: Get user timezone
        local_tz = pytz.timezone("Asia/Karachi")
        return {
            "Year": datetime.now(local_tz).strftime("%Y"),
            "Month": datetime.now(local_tz).strftime("%m"),
            "Day": datetime.now(local_tz).strftime("%d"),
            "Time": datetime.now(local_tz).strftime("%H:%M:%S"),
        }

    def _allowed_file(self, filename: str) -> bool:
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in self.config.ALLOWED_EXTENSIONS
        )
