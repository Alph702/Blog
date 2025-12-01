from datetime import datetime
from typing import Any, Dict, Optional, cast
from postgrest import APIResponse
from requests import Response
import requests
from werkzeug.datastructures import FileStorage
import uuid
from supabase import Client
import os
from pathlib import Path
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logger = logging.getLogger(__name__)


class WorkerService:
    upload_folder: Path = Path(os.path.join("/tmp", "uploads"))
    executors: Dict[str, ThreadPoolExecutor] = {
        "default": ThreadPoolExecutor(max_workers=1)
    }

    def __init__(self, supabase_client: Client, video_bucket: str):
        logger.debug("Initializing WorkerService")
        self.client: Client = supabase_client
        self.bucket: str = video_bucket
        os.makedirs(self.upload_folder, exist_ok=True)
        self.scheduler: BackgroundScheduler = BackgroundScheduler(
            executors=self.executors
        )
        self.scheduler.start()

    def _save_file(self, file: FileStorage) -> Dict[str, Any]:
        """Save file to storage and database."""
        try:
            logger.debug("Saving file to storage and database")
            try:
                filename: str = (
                    uuid.uuid4().hex + "." + str(file.filename).split(".")[-1]
                )
            except Exception as e:
                logger.critical(f"Error generating filename: {e}")
                raise RuntimeError(f"Error generating filename: {e}")
            filepath: str = f"{self.client.supabase_url}/storage/v1/object/public/{self.bucket}/upload/{filename}"
            # Upload to storage
            try:
                self.client.storage.from_(self.bucket).upload(
                    f"upload/{filename}",
                    file.read(),
                    {"content-type": file.content_type},
                )
            except Exception as e:
                logger.error(f"Error uploading file to storage: {e}", exc_info=True)
                raise RuntimeError(f"Error uploading file to storage: {e}")

            # Insert record
            try:
                self.client.table("videos").insert(
                    {"filename": filename, "filepath": filepath}
                ).execute()
            except Exception as e:
                logger.error(
                    f"Error inserting file record into database: {e}", exc_info=True
                )
                raise RuntimeError(f"Error inserting file record into database: {e}")

            # Get ID
            try:
                response = cast(
                    "APIResponse",
                    self.client.table("videos")
                    .select("id")
                    .eq("filepath", filepath)
                    .execute(),
                )
                data = response.data
                file_id: Optional[int] = None
                if isinstance(data, list) and data:
                    first_row = data[0]
                    if isinstance(first_row, dict) and "id" in first_row:
                        file_id = first_row["id"]
            except Exception as e:
                logger.error(
                    f"Error retrieving file ID from database: {e}", exc_info=True
                )
                raise RuntimeError(f"Error retrieving file ID from database: {e}")

            return {
                "message": "File uploaded successfully",
                "filename": filename,
                "file_id": file_id,
            }
        except Exception as e:
            logger.critical(f"Error saving file: {e}")
            raise RuntimeError(f"Error saving file: {e}")

    def _process_file(self, file_id: str, filepath: str, filename: str) -> None:
        """Process the uploaded file."""
        try:
            video_file_path: Path = Path(f"{self.upload_folder}/{filename}")
            try:
                with open(video_file_path, "wb") as video_file:
                    video = self.client.storage.from_(self.bucket).download(
                        "upload" + "/" + filename
                    )
                    video_file.write(video)
            except Exception as e:
                raise RuntimeError(f"Error downloading file from storage: {e}")
            try:
                self.client.table("videos").update({"status": "processing"}).eq(
                    "id", file_id
                ).execute()
                with open(video_file_path, "rb") as video:
                    res: Response = requests.post(
                        f"https://ffmpeg.pythonanywhere.com/upload/{file_id}",  # Video processing Microservice
                        files={"file": video},
                    )
                    if res.ok:
                        file_path = res.json().get("master_playlist")
                    else:
                        file_path = filepath
                        raise RuntimeError(f"Error processing video: {res.text}")
                self.client.table("videos").update(
                    {"status": "processed", "filepath": file_path}
                ).eq("id", file_id).execute()
                self.client.storage.from_(self.bucket).remove([f"upload/{filename}"])
            except Exception as e:
                self.client.table("videos").update({"status": "failed"}).eq(
                    "id", file_id
                ).execute()
                raise RuntimeError(f"Error processing file: {e}")
        except Exception as e:
            logger.critical(f"Error in processing file: {e}")
            raise RuntimeError(f"Error in processing file: {e}")

    def queue_file(self, file: FileStorage) -> Optional[int]:
        """Queue file for async processing."""
        try:
            try:
                save_result: Dict[str, Any] = self._save_file(file)
                file_id: str = str(save_result.get("file_id"))
                file_name: str = save_result.get("filename", "unknown")
                file_path: str = save_result.get("filepath", "")
            except Exception as e:
                raise RuntimeError(f"Error saving file: {e}")
            try:
                self.scheduler.add_job(
                    func=self._process_file,
                    trigger="date",
                    run_date=datetime.now(),
                    args=[file_id, file_path, file_name],
                    misfire_grace_time=3600,
                    coalesce=True,
                    id=f"process_{file_id}",
                    replace_existing=True,
                )
            except Exception as e:
                raise RuntimeError(f"Error scheduling file processing: {e}")
            return int(file_id)
        except Exception as e:
            logger.error(f"Error queueing file: {e}", exc_info=True)
            raise RuntimeError(f"Error queueing file: {e}")

    def __del__(self):
        logger.debug("Shutting down WorkerService.")
        self.scheduler.shutdown()
