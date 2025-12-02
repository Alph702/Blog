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

logger = logging.getLogger("worker.service")


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
            logger.debug(f"_save_file() called with filename: {file.filename}")
            try:
                logger.debug("Generating UUID for filename")
                filename: str = (
                    uuid.uuid4().hex + "." + str(file.filename).split(".")[-1]
                )
            except Exception as e:
                logger.critical(f"Error generating filename: {e}")
                raise RuntimeError(f"Error generating filename: {e}")
            filepath: str = f"{self.client.supabase_url}/storage/v1/object/public/{self.bucket}/upload/{filename}"
            # Upload to storage
            logger.debug(f"Uploading file to storage bucket: {self.bucket}")
            try:
                self.client.storage.from_(self.bucket).upload(
                    f"upload/{filename}",
                    file.read(),
                    {"content-type": file.content_type},
                )
                logger.debug("File uploaded to storage successfully")
            except Exception as e:
                logger.error(f"Error uploading file to storage: {e}", exc_info=True)
                raise RuntimeError(f"Error uploading file to storage: {e}")

            # Insert record
            logger.debug("Inserting file record into database")
            try:
                self.client.table("videos").insert(
                    {"filename": filename, "filepath": filepath}
                ).execute()
                logger.debug("File record inserted successfully")
            except Exception as e:
                logger.error(
                    f"Error inserting file record into database: {e}", exc_info=True
                )
                raise RuntimeError(f"Error inserting file record into database: {e}")

            # Get ID
            logger.debug("Retrieving file ID from database")
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
        logger.debug(
            f"_process_file() called for file_id: {file_id}, filename: {filename}"
        )
        try:
            video_file_path: Path = Path(f"{self.upload_folder}/{filename}")
            logger.debug(f"Video file path: {video_file_path}")
            try:
                with open(video_file_path, "wb") as video_file:
                    logger.debug(f"Downloading file from storage to {video_file_path}")
                    video = self.client.storage.from_(self.bucket).download(
                        "upload" + "/" + filename
                    )
                    logger.debug(f"Downloaded {len(video)} bytes")
                    video_file.write(video)
            except Exception as e:
                raise RuntimeError(f"Error downloading file from storage: {e}")
            try:
                logger.debug(
                    f"Updating video status to 'processing' for file_id: {file_id}"
                )
                self.client.table("videos").update({"status": "processing"}).eq(
                    "id", file_id
                ).execute()
                logger.debug(
                    f"Sending video to ffmpeg microservice for file_id: {file_id}"
                )
                with open(video_file_path, "rb") as video:
                    res: Response = requests.post(
                        f"https://ffmpeg.pythonanywhere.com/upload/{file_id}",  # Video processing Microservice
                        files={"file": video},
                    )
                    logger.debug(f"Microservice response status: {res.status_code}")
                    if res.ok:
                        logger.debug("Microservice processing succeeded")
                        file_path = res.json().get("master_playlist")
                    else:
                        logger.error(f"Microservice error: {res.text}")
                        file_path = filepath
                        raise RuntimeError(f"Error processing video: {res.text}")
                logger.debug(
                    f"Updating video status to 'processed' for file_id: {file_id}"
                )
                self.client.table("videos").update(
                    {"status": "processed", "filepath": file_path}
                ).eq("id", file_id).execute()
                logger.debug(
                    f"Removing upload file from storage for file_id: {file_id}"
                )
                self.client.storage.from_(self.bucket).remove([f"upload/{filename}"])
            except Exception as e:
                logger.debug(f"Setting video status to 'failed' for file_id: {file_id}")
                self.client.table("videos").update({"status": "failed"}).eq(
                    "id", file_id
                ).execute()
                raise RuntimeError(f"Error processing file: {e}")
        except Exception as e:
            logger.critical(f"Error in processing file: {e}")
            raise RuntimeError(f"Error in processing file: {e}")

    def queue_file(self, file: FileStorage) -> Optional[int]:
        """Queue file for async processing."""
        logger.debug(f"queue_file() called with filename: {file.filename}")
        try:
            try:
                logger.debug("Calling _save_file()")
                save_result: Dict[str, Any] = self._save_file(file)
                logger.debug("_save_file() completed successfully")
                file_id: str = str(save_result.get("file_id"))
                file_name: str = save_result.get("filename", "unknown")
                file_path: str = save_result.get("filepath", "")
                logger.debug(f"File saved: file_id={file_id}, filename={file_name}")
            except Exception as e:
                raise RuntimeError(f"Error saving file: {e}")
            try:
                logger.debug(f"Scheduling file processing job for file_id: {file_id}")
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
                logger.debug(f"Job scheduled successfully for file_id: {file_id}")
            except Exception as e:
                raise RuntimeError(f"Error scheduling file processing: {e}")
            return int(file_id)
        except Exception as e:
            logger.error(f"Error queueing file: {e}", exc_info=True)
            raise RuntimeError(f"Error queueing file: {e}")

    def __del__(self):
        logger.debug("Shutting down WorkerService.")
        self.scheduler.shutdown()
