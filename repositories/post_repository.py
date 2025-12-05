from typing import List, Dict, Optional, Any
from supabase import Client
from container import Config
from werkzeug.datastructures import FileStorage
import logging

logger = logging.getLogger("post.repository")


class PostRepository:
    def __init__(self, client: Client):
        logger.debug("Initializing PostRepository.")
        self.client: Client = client

    def _extract_records(self, data: Any) -> List[Dict[str, Any]]:
        """Normalize response.data into a list of dict records."""
        try:
            logger.debug(
                f"_extract_records() called with data type: {type(data).__name__}"
            )
            if isinstance(data, dict):
                logger.debug("Data is dict, wrapping in list")
            if isinstance(data, dict):
                logger.debug("Data is dict, wrapping in list")
                return [data]
            if isinstance(data, (list, tuple)):
                logger.debug(f"Data is sequence with {len(data)} items")
                return [item for item in data if isinstance(item, dict)]
            logger.debug("Data is empty or unrecognized type")
            return []
        except Exception as e:
            logger.error(f"Error extracting records: {e}", exc_info=True)
            raise RuntimeError(f"Error extracting records: {e}")

    def get_all(
        self, limit: int = 10, offset: int = 0, order_by: str = "id"
    ) -> List[Dict[str, Any]]:
        """Fetch all posts with pagination and ordering."""
        logger.debug(
            f"get_all() called - limit: {limit}, offset: {offset}, order_by: {order_by}"
        )
        try:
            logger.debug("Querying posts table")
            response = (
                self.client.table("posts")
                .select("*")
                .order(order_by, desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            logger.debug(
                f"Query executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.debug("Error in response, returning empty list")
                return []
            data = getattr(response, "data", None)
            logger.debug(f"Extracting {len(getattr(response, 'data', []))} records")
            return self._extract_records(data)
        except Exception as e:
            logger.error(f"Error fetching posts: {e}", exc_info=True)
            raise RuntimeError(f"Error fetching posts: {e}")

    def get_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a post by its ID."""
        logger.debug(f"get_by_id() called with post_id: {post_id}")
        try:
            logger.debug("Querying posts table for single record")
            response = (
                self.client.table("posts")
                .select("*")
                .eq("id", post_id)
                .single()
                .execute()
            )
            logger.debug(
                f"Query executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.debug("Error in response, returning None")
                return None
            data = getattr(response, "data", None)
            logger.debug("Extracting record from response")
            records = self._extract_records(data)
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Error fetching post with id=({post_id}): {e}", exc_info=True)
            raise RuntimeError(f"Error fetching post with id=({post_id}): {e}")

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new post."""
        logger.debug(f"create() called with title: {data.get('title')}")
        try:
            logger.debug("Inserting new post record")
            response = self.client.table("posts").insert(data).execute()
            logger.debug(
                f"Insert executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.error(
                    f"Error creating post: {getattr(response, 'error', 'Unknown error')}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Error creating post: {getattr(response, 'error', 'Unknown error')}"
                )
            logger.debug("Extracting created record from response")
            records = self._extract_records(getattr(response, "data", None))
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Error creating post: {e}", exc_info=True)
            raise RuntimeError(f"Error creating post: {e}")

    def update(self, post_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing post."""
        logger.debug(
            f"update() called with post_id: {post_id}, data keys: {list(data.keys())}"
        )
        try:
            logger.debug("Updating post record")
            response = (
                self.client.table("posts").update(data).eq("id", post_id).execute()
            )
            logger.debug(
                f"Update executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.error(
                    f"Error updating post: {getattr(response, 'error', 'Unknown error')}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Error updating post: {getattr(response, 'error', 'Unknown error')}"
                )
            logger.debug("Extracting updated record from response")
            records = self._extract_records(getattr(response, "data", None))
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Error updating post: {e}", exc_info=True)
            raise RuntimeError(f"Error updating post: {e}")

    def delete(self, post_id: int):
        """Delete a post by its ID."""
        logger.debug(f"delete() called with post_id: {post_id}")
        try:
            logger.debug("Deleting post record")
            self.client.table("posts").delete().eq("id", post_id).execute()
            logger.debug(f"Post {post_id} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting post: {e}", exc_info=True)
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
        logger.debug(
            f"filter_by_date() called - year: {year}, month: {month}, day: {day}"
        )
        posts: List[Dict[str, Any]] = []
        try:
            logger.debug("Building query with date filters")
            query = (
                self.client.table("posts")
                .select("*")
                .order(order_by, desc=True)
                .limit(limit)
                .offset(offset)
            )

            if year != "any":
                logger.debug(f"Adding year filter: {year}")
                query = query.eq("year", year)
            if month != "any":
                logger.debug(f"Adding month filter: {month}")
                query = query.eq("month", month)
            if day != "any":
                logger.debug(f"Adding day filter: {day}")
                query = query.eq("day", day)

            logger.debug("Executing filtered query")
            response = query.execute()
            logger.debug(
                f"Query executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                logger.error(
                    f"Error filtering posts: {getattr(response, 'error', 'Unknown error')}",
                    exc_info=True,
                )
                return []

            data = getattr(response, "data", None)
            logger.debug("Extracting filtered records")
            posts = self._extract_records(data)
            return posts
        except Exception as e:
            logger.error(f"Error filtering posts: {e}", exc_info=True)
            raise RuntimeError(f"Error filtering posts: {e}")

    def upload_file(self, file: FileStorage, file_name: str) -> Optional[str]:
        """Upload a file to Supabase storage and return its public URL."""
        logger.debug(f"upload_file() called with file_name: {file_name}")
        try:
            try:
                logger.debug("Reading file into memory")
                file_bytes = file.read()
                logger.debug(f"File read: {len(file_bytes)} bytes")
            except Exception as e:
                file_bytes = None
                logger.error(
                    f"Failed to read uploaded file into memory: {e}", exc_info=True
                )
                raise RuntimeError(f"Failed to read uploaded file into memory: {e}")

            if file_bytes:
                image_url: Optional[str] = None
                try:
                    try:
                        logger.debug(
                            f"Uploading file to bucket: {Config.BLOG_IMAGES_BUCKET}"
                        )
                        self.client.storage.from_(Config.BLOG_IMAGES_BUCKET).upload(
                            file_name, file_bytes, {"content-type": file.content_type}
                        )
                        logger.debug("File uploaded successfully")
                        image_url = f"{Config.SUPABASE_URL}/storage/v1/object/public/{Config.BLOG_IMAGES_BUCKET}/{file_name}"
                    except Exception as e:
                        logger.warning(
                            f"Initial upload failed, attempting to handle conflict: {e}"
                        )
                        if int(getattr(e, "status", "unknown")) == 409:
                            image_url = f"{Config.SUPABASE_URL}/storage/v1/object/public/{Config.BLOG_IMAGES_BUCKET}/{file_name}"
                        else:
                            image_url = None
                            logger.error(
                                f"Failed to upload file to Supabase storage: {e} with status {getattr(e, 'status', 'unknown')}",
                                exc_info=True,
                            )
                            raise RuntimeError(
                                f"Failed to upload file to Supabase storage: {e} with status {getattr(e, 'status', 'unknown')}"
                            )
                except Exception as e:
                    image_url = None
                    logger.error(
                        f"Error during file upload process: {e}", exc_info=True
                    )
                    raise RuntimeError(f"Error during file upload process: {e}")
                return image_url
            return None
        except Exception as e:
            logger.error(f"Error uploading file: {e}", exc_info=True)
            raise RuntimeError(f"Error uploading file: {e}")

    def has_next_page(self, page: int) -> bool:
        """Check if there is a next page of posts."""
        logger.debug(f"has_next_page() called with page: {page}")
        try:
            offset = page * Config.POSTS_PER_PAGE
            logger.debug(f"Checking for posts at offset: {offset}")
            response = (
                self.client.table("posts")
                .select("id")
                .offset(offset)
                .limit(1)
                .execute()
            )
            logger.debug(
                f"Query executed, response error: {getattr(response, 'error', None)}"
            )
            if getattr(response, "error", None):
                return False
            data = getattr(response, "data", None)
            records = self._extract_records(data)
            count = len(records)
            logger.debug(f"Found {count} record(s), has_next: {count > 0}")
            return True if count > 0 else False
        except Exception:
            logger.error("Error checking for next page.", exc_info=True)
            raise RuntimeError("Error checking for next page.")

    def get_new_id(self) -> int:
        try:
            logger.debug("Fetching latest post ID to generate new ID")
            response = self.client.table("posts").select("id").order("id", desc=True).limit(1).execute()
            if getattr(response, "error", None):
                logger.error(
                    f"Error fetching latest ID: {getattr(response, 'error', 'Unknown error')}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Error fetching latest ID: {getattr(response, 'error', 'Unknown error')}"
                )
            logger.debug("Extracting latest ID from response")
            data = getattr(response, "data", None)
            logger.debug(f"Data received for latest ID: {data}")
            records = self._extract_records(data)
            logger.debug(f"Latest record found: {records}")
            if records:
                id: int = records[0]["id"] + 1
                logger.debug(f"New ID generated: {id}")
                return id
            return 1
        except Exception as e:
            logger.error(f"Error fetching latest ID: {e}", exc_info=True)
            raise RuntimeError(f"Error fetching latest ID: {e}")

    def __del__(self):
        logger.debug("Destroying PostRepository instance.")
