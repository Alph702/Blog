# FFmpeg Microservice Documentation

This document provides a comprehensive guide to the FFmpeg microservice used for video processing in the project. The microservice is a Flask application designed to be deployed on a platform like PythonAnywhere. It receives video files, transcodes them into multiple quality levels using HLS (HTTP Live Streaming), and uploads the resulting video segments and playlists to a Supabase storage bucket.

## 1. FFmpeg Installation

The microservice relies on a specific version of FFmpeg to be present on the server. The following steps outline how to download and install the required FFmpeg build.

```bash
# 1. Download the latest FFmpeg build
wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n7.1-latest-linux64-gpl-shared-7.1.tar.xz -O ffmpeg-n7.1-latest-linux64-gpl-shared-7.1.tar.xz

# 2. Extract the archive
tar -xf ffmpeg-n7.1-latest-linux64-gpl-shared-7.1.tar.xz

# 3. Navigate into the extracted directory
cd ffmpeg-n7.1-latest-linux64-gpl-shared-7.1/

# 4. Move the shared libraries to the bin directory for easier access
mv lib/* bin

# 5. Remove the empty lib directory
rm -d lib/
```

After these steps, the `ffmpeg` and `ffprobe` executables will be located in the `bin` directory and are ready to be used by the microservice.

## 2. Microservice Overview

The core of the microservice is a Python Flask application that exposes endpoints to handle video uploads and processing.

### Key Functionalities:

*   **Video Upload:** Receives a video file associated with a unique `video_id`.
*   **Audio Detection:** Uses `ffprobe` to check if the uploaded video contains an audio stream.
*   **HLS Transcoding:** Transcodes the video into four different resolutions and bitrates for adaptive streaming:
    *   1080p (3000k)
    *   720p (1500k)
    *   480p (800k)
    *   360p (400k)
*   **Master Playlist Generation:** Creates a master `.m3u8` playlist that references all the different quality streams.
*   **Supabase Integration:** Uploads the generated HLS playlists (`.m3u8` files) and video segments (`.ts` files) to a specified Supabase storage bucket.
*   **Cleanup:** Removes the original uploaded file and the processed files from the local server after a successful upload to Supabase.
*   **Logging:** Maintains a detailed log file (`ffmpeg_app.log`) to track all operations, commands, and errors.

## 3. API Endpoints

### `POST /upload/<video_id>`

This is the main endpoint for processing a video.

*   **URL Parameter:**
    *   `video_id` (string): A unique identifier for the video. This ID is used to create a directory structure in the Supabase bucket.
*   **Request Body:**
    *   `multipart/form-data` with a single file field named `file`. The value should be the video file to be processed.
*   **Successful Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:**
        ```json
        {
          "ok": true,
          "video_id": "your_video_id",
          "has_audio": true,
          "message": "video processed successfully!",
          "master_playlist": "https://<your-supabase-url>/storage/v1/object/public/blog_videos/your_video_id/master.m3u8"
        }
        ```
*   **Error Response (4xx/5xx):**
    *   **Content-Type:** `application/json`
    *   **Body:**
        ```json
        {
          "error": "A descriptive error message."
        }
        ```

### `GET /`

A simple endpoint to check if the service is running.

*   **Successful Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:**
        ```json
        {
            "message": "🎬 Welcome to FFmpeg HLS Processor with Full Logging!",
            "upload_endpoint": "/upload/<video_id>",
            "example_video": "/videos/<video_id>/master.m3u8"
        }
        ```

## 4. Environment Variables

The microservice requires a `.env` file to be present in its root directory (`/home/ffmpeg/ffmpeg/.env` in the provided code) with the following variables:

*   `SUPABASE_URL`: The URL of your Supabase project.
*   `SUPABASE_SERVICE_ROLE_KEY`: The service role key for your Supabase project. This is required for uploading files to storage from a backend environment.
*   `BLOG_VIDEOS_BUCKET`: The name of the Supabase storage bucket where the processed videos will be stored (e.g., `blog_videos`).

**Example `.env` file:**

```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
BLOG_VIDEOS_BUCKET=blog_videos
```

## 5. Video Processing Workflow

1.  The main application sends a `POST` request to the `/upload/<video_id>` endpoint of the FFmpeg microservice with the raw video file.
2.  The microservice saves the file to a temporary `uploads` directory.
3.  It checks for the presence of an audio stream using `ffprobe`.
4.  It runs a series of `ffmpeg` commands to transcode the video into multiple HLS streams. Each stream (resolution) is placed in its own subdirectory.
5.  A `master.m3u8` playlist is created, pointing to the individual stream playlists.
6.  The entire directory containing the master playlist and all video segments is uploaded to the Supabase storage bucket under a path corresponding to the `video_id`.
7.  After a successful upload, the temporary files and directories on the microservice's local filesystem are deleted.
8.  The microservice returns a JSON response containing the public URL to the master playlist on Supabase.

## Code
```python
import os
import sys
import json
import subprocess
import shutil
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort
from dotenv import load_dotenv
from supabase import create_client

# -------------------------
# Setup Logging
# -------------------------
LOG_FILE = "ffmpeg_app.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.getLogger().addHandler(console_handler)

# -------------------------
# Load Environment Variables
# -------------------------
load_dotenv('/home/ffmpeg/ffmpeg/.env')

UPLOAD_FOLDER = os.path.join("ffmpeg", "static", "uploads")
OUTPUT_FOLDER = os.path.join("ffmpeg", "static", "videos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = (
    os.getenv('SUPABASE_SERVICE_ROLE_KEY') or
    os.getenv('SUPERBASE_SERVICE_ROLE_KEY') or
    os.getenv('SUPABASE_ANON_KEY') or
    os.getenv('SUPABASE_ANON_KEY')
)
BLOG_VIDEOS_BUCKET = (
    os.getenv('BLOG_VIDEOS_BUCKET') or
    os.getenv('SUPABASE_VIDEOS_BUCKET_NAME') or
    'blog_videos'
)

if os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPERBASE_SERVICE_ROLE_KEY'):
    logging.warning("⚠️ Using Supabase service role key. Keep it secret!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# Initialize Flask
# -------------------------
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# -------------------------
# Utility Functions
# -------------------------
def log_cmd(cmd):
    logging.info(f"Running command: {' '.join(cmd)}")

def has_audio(input_file: str) -> bool:
    """Check if file has audio using ffprobe"""
    ffprobe_path = "ffprobe" if sys.platform != "linux" else os.path.join(os.path.dirname(__file__), "ffmpeg", "bin", "ffprobe")
    cmd = [
        ffprobe_path,
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "json",
        input_file
    ]
    log_cmd(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout or "{}")
        has_audio_stream = len(info.get("streams", [])) > 0
        logging.info(f"Audio detection for {input_file}: {has_audio_stream}")
        return has_audio_stream
    except subprocess.CalledProcessError as e:
        logging.error(f"FFprobe error for {input_file}: {e}")
        return False

def upload_folder_to_supabase(folder_path: str):
    logging.info(f"Uploading folder {folder_path} to Supabase bucket '{BLOG_VIDEOS_BUCKET}'")
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            try:
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, start=folder_path)
                upload_path = f"{os.path.basename(folder_path)}/{relative_path.replace(os.sep, '/')}"
                logging.debug(f"Uploading {file_path} as {upload_path}")
                with open(file_path, "rb") as f:
                    data = f.read()
                supabase.storage.from_(BLOG_VIDEOS_BUCKET).upload(upload_path, data, {'cacheControl': '3600'})
                logging.info(f"Uploaded {upload_path}")
            except Exception as e:
                logging.error(f"Error uploading {file_path}: {e}")

def run_ffmpeg_sync(cmd: list):
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"FFmpeg failed with error: {result.stderr}")
        raise Exception(result.stderr)
    logging.info("FFmpeg command completed successfully")
    return result

# -------------------------
# Routes
# -------------------------
@app.route("/")
def index():
    logging.info("Accessed / endpoint")
    return jsonify({
        "message": "🎬 Welcome to FFmpeg HLS Processor with Full Logging!",
        "upload_endpoint": "/upload/<video_id>",
        "example_video": "/videos/<video_id>/master.m3u8"
    })

@app.route("/upload/<video_id>", methods=["POST"])
def upload_video(video_id):
    logging.info(f"Upload request received for video_id: {video_id}")
    file = request.files.get("file")
    if not file:
        logging.warning("No file uploaded")
        return jsonify({"error": "No file uploaded"}), 400

    upload_path = os.path.join(UPLOAD_FOLDER, f"{video_id}.mp4")
    file.save(upload_path)
    logging.info(f"File saved to {upload_path}")

    out_dir = os.path.join(OUTPUT_FOLDER, video_id)
    os.makedirs(out_dir, exist_ok=True)
    logging.info(f"Output directory created: {out_dir}")

    ffmpeg_path = "ffmpeg" if sys.platform != "linux" else os.path.join(os.path.dirname(__file__), "ffmpeg", "bin", "ffmpeg")

    audio_exists = has_audio(upload_path)

    streams = [
        {"bitrate": "3000k", "resolution": "1920x1080", "label": "v0"},
        {"bitrate": "1500k", "resolution": "1280x720", "label": "v1"},
        {"bitrate": "800k", "resolution": "854x480", "label": "v2"},
        {"bitrate": "400k", "resolution": "640x360", "label": "v3"},
    ]

    # Encode each stream
    for stream in streams:
        stream_label = stream["label"]
        stream_out_dir = os.path.join(out_dir, stream_label)
        os.makedirs(stream_out_dir, exist_ok=True)
        logging.info(f"Processing stream {stream_label} -> {stream_out_dir}")

        cmd = [
            ffmpeg_path,
            "-y", "-i", upload_path,
            "-map", "v:0",
            * (["-map", "a:0"] if audio_exists else []),
            "-c:v", "libx264",
            * (["-c:a", "aac"] if audio_exists else []),
            "-b:v", stream["bitrate"],
            "-s", stream["resolution"],
            "-preset", "veryfast",
            "-threads", "1",
            "-g", "48", "-sc_threshold", "0", "-keyint_min", "48",
            "-hls_time", "2",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", os.path.join(stream_out_dir, "segment_%03d.ts"),
            "-f", "hls", os.path.join(stream_out_dir, "prog_index.m3u8")
        ]
        try:
            run_ffmpeg_sync(cmd)
        except Exception as e:
            logging.error(f"FFmpeg stream {stream_label} failed: {e}")
            return jsonify({"error": f"FFmpeg stream {stream_label} failed"}), 500

    # Master playlist
    try:
        master_path = os.path.join(out_dir, "master.m3u8")
        logging.info(f"Creating master playlist at {master_path}")
        with open(master_path, "w") as m3u:
            m3u.write("#EXTM3U\n")
            m3u.write("#EXT-X-VERSION:3\n\n")
            for stream in streams:
                m3u.write(
                    f"#EXT-X-STREAM-INF:BANDWIDTH={int(stream['bitrate'].replace('k','000'))},RESOLUTION={stream['resolution']}\n"
                )
                m3u.write(f"{stream['label']}/prog_index.m3u8\n")
    except Exception as e:
        logging.error(f"Master playlist creation failed: {e}")
        return jsonify({"error": "FFmpeg Master Playlist failed"}), 500

    # Upload to Supabase
    try:
        upload_folder_to_supabase(out_dir)
        os.remove(upload_path)
        shutil.rmtree(out_dir, ignore_errors=True)
        logging.info("Upload and cleanup completed successfully")
    except Exception as e:
        logging.error(f"Upload/Cleanup error: {e}")
        return jsonify({"error": "Supabase upload failed"}), 500

    return jsonify({
        "ok": True,
        "video_id": video_id,
        "has_audio": audio_exists,
        "message": "video processed successfully!",
        "master_playlist": f"{SUPABASE_URL}/storage/v1/object/public/{BLOG_VIDEOS_BUCKET}/{video_id}/master.m3u8"
    })

@app.route("/videos/<video_id>/<path:filename>")
def serve_video(video_id, filename):
    logging.info(f"Request for video file: {video_id}/{filename}")
    video_dir = os.path.join(OUTPUT_FOLDER, video_id)
    file_path = os.path.join(video_dir, filename)
    if not os.path.exists(file_path):
        logging.warning(f"File not found: {file_path}")
        abort(404, description="Video file not found")
    return send_from_directory(video_dir, filename, as_attachment=False)

# -------------------------
# Run Flask
# -------------------------
if __name__ == "__main__":
    logging.info("Starting FFmpeg Flask Server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
```