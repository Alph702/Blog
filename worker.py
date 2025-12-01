import os
import uuid
from datetime import datetime

import requests
import supabase
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Module logger for worker
logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, SUPABASE_KEY, SUPABASE_URL, videos_bucket="video"):
        self.upload_folder = os.path.join("/tmp", "uploads")
        os.makedirs(self.upload_folder, exist_ok=True)

        executors = {"default": ThreadPoolExecutor(max_workers=1)}
        self.scheduler = BackgroundScheduler(executors=executors)
        self.scheduler.start()
        self.SUPABASE_KEY = SUPABASE_KEY
        self.SUPABASE_URL = SUPABASE_URL
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL or SUPABASE_ANON_KEY is not set. Supabase operations will fail."
            )
        self.supabase_client = supabase.create_client(
            self.SUPABASE_URL, self.SUPABASE_KEY
        )
        self.videos_bucket = videos_bucket
        logger.info("Worker initialized and scheduler started")

    def save_file(self, file):
        filename = uuid.uuid4().hex + "." + file.filename.split(".")[-1]
        filepath = f"{self.SUPABASE_URL}/storage/v1/object/public/{self.videos_bucket}/upload/{filename}"
        self.supabase_client.storage.from_(self.videos_bucket).upload(
            "upload" + "/" + filename, file.read(), {"content-type": file.content_type}
        )
        self.supabase_client.table("videos").insert(
            {"filename": filename, "filepath": filepath}
        ).execute()
        file_id = (
            self.supabase_client.table("videos")
            .select("id")
            .eq("filepath", filepath)
            .execute()
            .data[0]["id"]
        )
        return {
            "message": "File uploaded successfully",
            "filename": filename,
            "file_id": file_id,
        }

    def queue_file(self, file_id):
        """Queue file for async processing."""
        self.scheduler.add_job(
            func=self._process_file,
            trigger="date",
            run_date=datetime.now(),
            args=[file_id],
            misfire_grace_time=3600,
            coalesce=True,
            id=f"process_{file_id}",
            replace_existing=True,
        )

    def _upload_folder_to_supabase(self, folder_path: str, bucket_name):
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                try:
                    file_path = os.path.join(root, file_name)
                    # Calculate relative path inside output folder
                    relative_path = os.path.relpath(file_path, start=folder_path)
                    upload_path = (
                        os.path.basename(folder_path)
                        + "/"
                        + relative_path.replace(os.path.sep, "/")
                    )  # Normalize for Supabase
                    with open(file_path, "rb") as f:
                        data = f.read()
                    # Upload using Supabase storage bucket, preserving folder structure with relative_path
                    self.supabase_client.storage.from_(bucket_name).upload(
                        upload_path, data, {"cacheControl": "3600"}
                    )
                except Exception as e:
                    logger.error(
                        f"Error uploading {file_path} to Supabase: {e}", exc_info=True
                    )

    def _process_file(self, file_id):
        result = (
            self.supabase_client.table("videos")
            .select("filepath", "filename")
            .eq("id", file_id)
            .execute()
        )
        if not result.data:
            raise ValueError(f"No file found with id {file_id}")
        result = result.data[0]
        filepath = result["filepath"]
        filename = result["filename"]
        video_file_path = self.upload_folder + "/" + filename
        with open(video_file_path, "wb") as video_file:
            video = self.supabase_client.storage.from_(self.videos_bucket).download(
                "upload" + "/" + filename
            )
            video_file.write(video)
        try:
            self.supabase_client.table("videos").update({"status": "processing"}).eq(
                "id", file_id
            ).execute()
            with open(video_file_path, "rb") as video:
                res = requests.post(
                    f"https://ffmpeg.pythonanywhere.com/upload/{file_id}",
                    files={"file": video},
                )
                if res.ok:
                    file_path = res.json().get("master_playlist")
                else:
                    file_path = filepath
                    raise RuntimeError(f"Error processing video: {res.text}")
            self.supabase_client.table("videos").update(
                {"status": "processed", "filepath": file_path}
            ).eq("id", file_id).execute()
            self.supabase_client.storage.from_(self.videos_bucket).remove(
                [f"upload/{filename}"]
            )
        except Exception as e:
            self.supabase_client.table("videos").update({"status": "failed"}).eq(
                "id", file_id
            ).execute()
            raise RuntimeError(f"Error processing file: {e}")
