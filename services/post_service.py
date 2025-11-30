from typing import List, Dict, Any, Optional, cast
from repositories import PostRepository
from .video_service import VideoService 
from dateutil import parser
from config import Config
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class PostService:
    def __init__(self, repo: PostRepository, video_service: VideoService):
        self.repo: PostRepository = repo
        self.video_service: VideoService = video_service
        self.config: Config = Config()
        self.limit: int = self.config.POSTS_PER_PAGE
        logger.info("PostService initialized!")

    def get_recent_posts(self, page: int = 1) -> List[Dict[str, Any]]:
        logger.debug(f"Fetching recent posts for page {page}")
        offset: int = (page - 1) * self.limit
        try:
            try:
                posts: List[Dict[str, Any]] = self.repo.get_all(
                    limit=self.limit, offset=offset, order_by="timestamp" or "id"
                )
            except Exception as e:
                logger.error(f"Error fetching posts from repository: {e}")
                raise Exception("Failed to retrieve posts.")

            logger.debug(f"Retrieved {len(posts)} posts from repository")
            try:
                for post in posts:
                    post["timestamps"] = self._format_date(
                        cast(int, post.get("created_year")),
                        cast(int, post.get("created_month")),
                        cast(int, post.get("created_day")),
                        cast(str, post.get("created_time")),
                    )
                    if post.get("video_id"):
                        post["video"] = self.video_service.get_video_by_id(post["video_id"])
                    
                    logger.debug(f"Post: {post}")
            except Exception as e:
                logger.error(f"Error processing posts: {e}")
                raise Exception("Failed to process posts.")
            return posts
        except Exception as e:
            logger.error(f"Error retrieving recent posts: {e}")
            raise Exception("Failed to retrieve recent posts.")

    def get_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        try:
            try:
                logger.debug(f"Fetching post by ID: {post_id}")
                post = self.repo.get_by_id(post_id)
            except Exception as e:
                logger.error(f"Error fetching post from repository: {e}")
                raise Exception("Failed to retrieve post.")
            logger.debug(f"Retrieved post: {post}")
            try:
                if post:
                    post["timestamps"] = self._format_date(
                        cast(int, post.get("created_year")),
                        cast(int, post.get("created_month")),
                        cast(int, post.get("created_day")),
                        cast(str, post.get("created_time")),
                    )
                    if post.get("video_id"):
                        post["video"] = self.video_service.get_video_by_id(post["video_id"])
                    return post
                else:
                    logger.warning(f"Post with ID {post_id} not found")
                    raise ValueError("Post not found")
            except ValueError as ve:
                logger.warning(f"ValueError: {ve}")
                raise
            except Exception as e:
                logger.error(f"Error processing post data: {e}")
                raise
        except Exception as e:
            logger.error(f"Error retrieving post by ID {post_id}: {e}")
            raise Exception("Failed to retrieve post By Id.")

    def create_post(
        self,
        title: Optional[str],
        content: str,
        image_url: Optional[str] = None,
        video_id: Optional[int] = None,
    ):
        try:
            try:
                timestamp: Dict[str, str] = self._get_current_timestamp()
                data = {
                    "title": title,
                    "content": content,
                    "image": image_url,
                    "video_id": video_id,
                    "created_year": timestamp["Year"],
                    "created_month": timestamp["Month"],
                    "created_day": timestamp["Day"],
                    "created_time": timestamp["Time"],
                }
            except Exception as e:
                logger.error(f"Error preparing post data for creation: {e}")
                raise ValueError("Invalid data for creating post.")
            logger.debug(f"Creating post with data: {data}")
            try:
                res = self.repo.create(data)
            except Exception as e:
                if getattr(e, 'code', None) == '23505':  # Unique violation
                    logger.warning("Post with the same id already exists.")
                    raise ValueError("Post with the same id already exists.")
                else:
                    logger.error(f"Error creating post in repository: {e}")
                    raise Exception("Failed to create post.")
        except ValueError as ve:
            logger.warning(f"ValueError: {ve}")
            raise Exception("Failed to create post.")
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            raise Exception("Failed to create post.")
        return res

    def update_post(
        self,
        post_id: int,
        title: Optional[str],
        content: str,
        image_file: Optional[FileStorage] = None,
        video_file: Optional[FileStorage] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            logger.debug(f"Updating post ID {post_id} with title: {title}, content length: {len(content)}")
            try:
                post_data = self.get_post_by_id(post_id)
                if not post_data:
                    logger.warning(f"Post with ID {post_id} not found for update")
                    raise ValueError("Post not found for update")
            except ValueError as ve:
                logger.warning(f"ValueError: {ve}")
                raise
            except Exception as e:
                logger.error(f"Error fetching post for update: {e}")
                raise

            update_data = {"title": title, "content": content}
            logger.debug(f"Initial update data: {update_data}")

            try:
                if image_file:
                    image_url = self.upload_image(image_file)
                    if image_url:
                        update_data["image"] = image_url
            except Exception as e:
                logger.error(f"Error uploading image: {e}")
                raise
            
            try:
                if video_file:
                    video_id = self.video_service.upload_video(video_file)
                    if video_id:
                        update_data["video_id"] = video_id
            except Exception as e:
                logger.error(f"Error uploading video: {e}")
                raise
            logger.debug(f"Final update data: {update_data}")
            try:
                res = self.repo.update(post_id, update_data)
            except Exception as e:
                logger.error(f"Error updating post in repository: {e}")
                raise
        except ValueError as ve:
            logger.warning(f"ValueError: {ve}")
            raise Exception("Failed to update post.")
        except Exception as e:
            logger.error(f"Error updating post ID {post_id}: {e}")
            raise Exception("Failed to update post.")
        return res

    def filter_posts(
        self, year: str, month: str, day: str, page: int = 1
    ) -> List[Dict[str, Any]]:
        try:
            try:
                logger.debug(f"Filtering posts by date - Year: {year}, Month: {month}, Day: {day}, Page: {page}")
                posts: List[Dict[str, Any]] = self.repo.filter_by_date(
                    year,
                    month,
                    day,
                    limit=self.limit,
                    offset=(page - 1) * self.limit,
                    order_by="id",
                )
            except Exception as e:
                logger.error(f"Error filtering posts: {e}")
                raise
            try:
                for post in posts:
                    post["formatted_timestamp"] = self._format_date(
                        cast(int, post.get("created_year")),
                        cast(int, post.get("created_month")),
                        cast(int, post.get("created_day")),
                        cast(str, post.get("created_time")),
                    )
                    if post.get("video_id"):
                        post["video"] = self.video_service.get_video_by_id(post["video_id"])
            except Exception as e:
                logger.error(f"Error processing filtered posts: {e}")
                raise
            return posts
        except Exception as e:
            logger.error(f"Error filtering posts by date: {e}")
            raise Exception("Failed to filter posts.")

    def delete_post(self, post_id: int):
        try:
            logger.debug(f"Deleting post with ID: {post_id}")
            self.repo.delete(post_id)
        except Exception as e:
            logger.error(f"Error deleting post ID {post_id}: {e}")
            raise Exception(f"Error deleting post ({post_id}).")

    def upload_image(self, file: FileStorage) -> Optional[str]:
        try:
            logger.debug(f"Uploading image with filename: {file.filename}")
            if file and self._allowed_file(str(file.filename)):
                filename = secure_filename(str(file.filename))
                try:
                    image_url: Optional[str] = self.repo.upload_file(file, filename)
                    return image_url
                except Exception as e:
                    logger.error(f"Error uploading file to repository: {e}")
                    raise
            else:
                return None
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            raise Exception("Failed to upload image.")

    def has_next_page(self, page: int) -> bool:
        try:            
            logger.debug(f"Checking for next page after page {page}")
            return self.repo.has_next_page(page)
        except Exception as e:
            logger.error(f"Error checking for next page: {e}")
            raise Exception("Failed to check for next page.")

    def _format_date(self, year: int, month: int, day: int, time: str) -> str:
        if not year or not month or not day or not time:
            return ""
        try:
            dt = parser.parse(f"{year}-{month}-{day} {time}").replace(tzinfo=None)
            return dt.strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            logger.warning(f"Failed to parse date: {year}-{month}-{day} {time}")
            return str(f"{year}-{month}-{day} {time}")

    def _get_current_timestamp(self) -> Dict[str, str]:
        from datetime import datetime
        import pytz

        try:
            utc = pytz.timezone("UTC")
            return {
                "Year": datetime.now(utc).strftime("%Y"),
                "Month": datetime.now(utc).strftime("%m"),
                "Day": datetime.now(utc).strftime("%d"),
                "Time": datetime.now(utc).strftime("%H:%M:%S"),
            }
        except Exception as e:
            logger.error(f"Error getting current timestamp: {e}")
            raise

    def _allowed_file(self, filename: str) -> bool:
        try:
            return (
                "." in filename
                and filename.rsplit(".", 1)[1].lower() in self.config.ALLOWED_EXTENSIONS
            )
        except Exception as e:
            logger.error(f"Error checking allowed file: {e}")
            raise

    def __del__(self):
        logger.info("PostService instance is being destroyed.")