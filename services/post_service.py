from typing import Dict, Optional
from repositories.post_repository import PostRepository, PostsModel, PostModel
from .video_service import VideoService
from dateutil import parser
from config import Config
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger("post.service")


class PostService:
    def __init__(self, repo: PostRepository, video_service: VideoService) -> None:
        self.repo: PostRepository = repo
        self.video_service: VideoService = video_service
        self.config: Config = Config()
        self.limit: int = self.config.POSTS_PER_PAGE
        logger.info("PostService initialized!")

    def get_recent_posts(self, page: int = 1) -> PostsModel:
        logger.debug(f"get_recent_posts() called with page: {page}")
        offset: int = (page - 1) * self.limit
        logger.debug(f"Calculated offset: {offset}, limit: {self.limit}")
        try:
            try:
                logger.debug("Calling repo.get_all() with pagination")
                posts: PostsModel = self.repo.get_all(
                    limit=self.limit, offset=offset, order_by="timestamp" or "id"
                )
            except Exception as e:
                logger.error(
                    f"Error fetching posts from repository: {e}", exc_info=True
                )
                raise Exception("Failed to retrieve posts.")

            logger.debug(f"Retrieved {len(posts.posts)} posts from repository")
            try:
                logger.debug("Processing posts and formatting timestamps")
                for post in posts.posts:
                    post.timestamps = self._format_date(
                        post.created_year,
                        post.created_month,
                        post.created_day,
                        post.created_time,
                    )
                    if post.video_id:
                        post.video = self.video_service.get_video_by_id(post.video_id)

                    logger.debug(f"Post: {post}")
            except Exception as e:
                logger.error(f"Error processing posts: {e}", exc_info=True)
                raise Exception("Failed to process posts.")
            return posts
        except Exception as e:
            logger.error(f"Error retrieving recent posts: {e}", exc_info=True)
            raise Exception("Failed to retrieve recent posts.")

    def get_post_by_id(self, post_id: int) -> Optional[PostModel]:
        try:
            try:
                logger.debug(f"get_post_by_id() called with post_id: {post_id}")
                logger.debug("Calling repo.get_by_id()")
                post = self.repo.get_by_id(post_id)
            except Exception as e:
                logger.error(f"Error fetching post from repository: {e}", exc_info=True)
                raise Exception("Failed to retrieve post.")
            logger.debug(f"Retrieved post: {post}")
            try:
                logger.debug("Processing post data and formatting timestamps")
                if post:
                    post.timestamps = self._format_date(
                        post.created_year,
                        post.created_month,
                        post.created_day,
                        post.created_time,
                    )
                    if post.video_id:
                        post.video = self.video_service.get_video_by_id(post.video_id)
                    return post
                else:
                    logger.warning(f"Post with ID {post_id} not found")
                    raise ValueError("Post not found")
            except ValueError as ve:
                logger.warning(f"ValueError: {ve}")
                raise
            except Exception as e:
                logger.error(f"Error processing post data: {e}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Error retrieving post by ID {post_id}: {e}", exc_info=True)
            raise Exception("Failed to retrieve post By Id.")

    def create_post(
        self,
        title: Optional[str],
        content: str,
        image_url: Optional[str] = None,
        video_id: Optional[int] = None,
    ) -> PostModel:
        logger.debug(f"create_post() called with title: {title}")
        try:
            try:
                logger.debug("Preparing post data")
                timestamp: Dict[str, str] = self._get_current_timestamp()
                post = PostModel(
                    id=self.repo.get_new_id(),
                    title=title,
                    content=content,
                    # TODO: Fix naming inconsistency
                    image=image_url,
                    video_id=video_id,
                    created_year=int(timestamp["Year"]),
                    created_month=int(timestamp["Month"]),
                    created_day=int(timestamp["Day"]),
                    created_time=timestamp["Time"],
                )
            except Exception as e:
                logger.error(
                    f"Error preparing post data for creation: {e}", exc_info=True
                )
                raise ValueError("Invalid data for creating post.")
            logger.debug(f"Creating post with data: {post.model_dump()}")
            try:
                logger.debug("Calling repo.create()")
                res = self.repo.create(post)
            except Exception as e:
                logger.error(f"Error creating post in repository: {e}", exc_info=True)
                raise Exception("Failed to create post.")
        except ValueError as ve:
            logger.warning(f"ValueError: {ve}")
            raise Exception("Failed to create post.")
        except Exception as e:
            logger.error(f"Error creating post: {e}", exc_info=True)
            raise Exception("Failed to create post.")
        return res

    def update_post(
        self,
        post_id: int,
        title: Optional[str],
        content: str,
        image_file: Optional[FileStorage] = None,
        video_file: Optional[FileStorage] = None,
        video_id: Optional[int] = None,
    ) -> Optional[PostModel]:
        try:
            logger.debug(
                f"update_post() called with post_id: {post_id}, title: {title}"
            )
            try:
                logger.debug(f"Fetching current post data for post_id: {post_id}")
                post = self.get_post_by_id(post_id)
                if not post:
                    logger.warning(f"Post with ID {post_id} not found for update")
                    raise ValueError("Post not found for update")
            except ValueError as ve:
                logger.warning(f"ValueError: {ve}")
                raise
            except Exception as e:
                logger.error(f"Error fetching post for update: {e}", exc_info=True)
                raise

            post.title = title
            post.content = content
            logger.debug(f"Initial update data: {post.model_dump()}")

            try:
                logger.debug("Checking for image file in update")
                if image_file:
                    image_url = self.upload_image(image_file)
                    if image_url:
                        post.image = image_url
            except Exception as e:
                logger.error(f"Error uploading image: {e}", exc_info=True)
                raise

            try:
                logger.debug("Checking for video in update")
                # Prioritize video_id if provided (pre-uploaded)
                if video_id:
                    logger.debug(f"Using pre-uploaded video_id: {video_id}")
                    post.video_id = video_id
                # Fallback to uploading video file if provided
                elif video_file:
                    uploaded_video_id = self.video_service.upload_video(video_file)
                    if uploaded_video_id:
                        post.video_id = uploaded_video_id
            except Exception as e:
                logger.error(f"Error handling video: {e}", exc_info=True)
                raise
            logger.debug(f"Final update data: {post.model_dump()}")
            try:
                logger.debug(f"Calling repo.update() for post_id: {post_id}")
                res = self.repo.update(post)
            except Exception as e:
                logger.error(f"Error updating post in repository: {e}", exc_info=True)
                raise
        except ValueError as ve:
            logger.warning(f"ValueError: {ve}")
            raise Exception("Failed to update post.")
        except Exception as e:
            logger.error(f"Error updating post ID {post_id}: {e}", exc_info=True)
            raise Exception("Failed to update post.")
        return res

    def filter_posts(
        self, year: str, month: str, day: str, page: int = 1
    ) -> PostsModel:
        try:
            try:
                logger.debug(
                    f"filter_posts() called - Year: {year}, Month: {month}, Day: {day}, Page: {page}"
                )
                logger.debug("Calling repo.filter_by_date()")
                posts: PostsModel = self.repo.filter_by_date(
                    year,
                    month,
                    day,
                    limit=self.limit,
                    offset=(page - 1) * self.limit,
                    order_by="id",
                )
            except Exception as e:
                logger.error(f"Error filtering posts: {e}", exc_info=True)
                raise
            try:
                for post in posts.posts:
                    post.timestamps = self._format_date(
                        post.created_year,
                        post.created_month,
                        post.created_day,
                        post.created_time,
                    )
                    if post.video_id:
                        post.video = self.video_service.get_video_by_id(post.video_id)
            except Exception as e:
                logger.error(f"Error processing filtered posts: {e}", exc_info=True)
                raise
            return posts
        except Exception as e:
            logger.error(f"Error filtering posts by date: {e}", exc_info=True)
            raise Exception("Failed to filter posts.")

    def delete_post(self, post_id: int) -> None:
        try:
            logger.debug(f"delete_post() called with post_id: {post_id}")
            logger.debug("Calling repo.delete()")
            self.repo.delete(post_id)
        except Exception as e:
            logger.error(f"Error deleting post ID {post_id}: {e}", exc_info=True)
            raise Exception(f"Error deleting post ({post_id}).")

    def upload_image(self, file: FileStorage) -> Optional[str]:
        try:
            logger.debug(f"upload_image() called with filename: {file.filename}")
            if file and self._allowed_file(str(file.filename)):
                logger.debug(f"File is allowed, uploading: {file.filename}")
                filename = secure_filename(str(file.filename))
                try:
                    image_url: Optional[str] = self.repo.upload_file(file, filename)
                    return image_url
                except Exception as e:
                    logger.error(
                        f"Error uploading file to repository: {e}", exc_info=True
                    )
                    raise
            else:
                return None
        except Exception as e:
            logger.error(f"Error uploading image: {e}", exc_info=True)
            raise Exception("Failed to upload image.")

    def upload_video(self, file: FileStorage) -> Optional[int]:
        try:
            logger.debug(f"upload_video() called with filename: {file.filename}")
            if file and self._allowed_file(str(file.filename)):
                logger.debug(f"File is allowed, uploading: {file.filename}")
                try:
                    video_id: Optional[int] = self.video_service.upload_video(file)
                    return video_id
                except Exception as e:
                    logger.error(
                        f"Error uploading video to video service: {e}", exc_info=True
                    )
                    raise
            else:
                return None
        except Exception as e:
            logger.error(f"Error uploading video: {e}", exc_info=True)
            raise Exception("Failed to upload video.")

    def has_next_page(self, page: int) -> bool:
        try:
            logger.debug(f"has_next_page() called with page: {page}")
            logger.debug("Calling repo.has_next_page()")
            return self.repo.has_next_page(page)
        except Exception as e:
            logger.error(f"Error checking for next page: {e}", exc_info=True)
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
            logger.error(f"Error getting current timestamp: {e}", exc_info=True)
            raise

    def _allowed_file(self, filename: str) -> bool:
        try:
            return (
                "." in filename
                and filename.rsplit(".", 1)[1].lower() in self.config.ALLOWED_EXTENSIONS
            )
        except Exception as e:
            logger.error(f"Error checking allowed file: {e}", exc_info=True)
            raise
