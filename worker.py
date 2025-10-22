import os, subprocess, supabase, uuid, shutil
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
 
class Worker:
    def __init__(self, videos_bucket='Videos'):
        self.upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        self.output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)

        executors = {'default': ThreadPoolExecutor(max_workers=2)}
        self.scheduler = BackgroundScheduler(executors=executors)
        self.scheduler.start()

        self.SUPABASE_KEY = (
            os.getenv('SUPABASE_SERVICE_ROLE_KEY') or
            os.getenv('SUPERBASE_SERVICE_ROLE_KEY') or
            os.getenv('SUPERBASE_ANON_KEY') or
            os.getenv('SUPABASE_ANON_KEY')
        )
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            print("Warning: SUPABASE_URL or SUPERBASE_ANON_KEY is not set. Supabase operations will likely fail.")
        self.supabase_client = supabase.create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
        self.videos_bucket = videos_bucket

    def save_file(self, file):
        filename = uuid.uuid4().hex + '.' + file.filename.split('.')[-1]
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)
        self.supabase_client.table('videos').insert({'filename': filename, 'filepath': filepath}).execute()
        file_id = self.supabase_client.table('videos').select('id').eq('filepath', filepath).execute().data[0]['id']
        return {"message": "File uploaded successfully", "filename": filename, 'file_id': file_id}
    
    def queue_file(self, file_id):
        """Queue file for async processing."""
        self.scheduler.add_job(
            func=self._process_file,
            trigger='date',
            run_date=datetime.now(),
            args=[file_id],
            misfire_grace_time=3600,
            coalesce=True,
            id=f"process_{file_id}",
            replace_existing=True
        )

    def _upload_folder_to_supabase(self, folder_path: str, bucket_name):
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                try:
                    file_path = os.path.join(root, file_name)
                    # Calculate relative path inside output folder
                    relative_path = os.path.relpath(file_path, start=folder_path)
                    upload_path = folder_path.split("\\")[-1] + "/" + relative_path.replace("\\", "/")  # Normalize for Supabase
                    with open(file_path, "rb") as f:
                        data = f.read()
                    # Upload using Supabase storage bucket, preserving folder structure with relative_path
                    self.supabase_client.storage.from_(bucket_name).upload(upload_path, data, {'cacheControl': '3600'})
                except Exception as e:
                    print(f"Error uploading {file_path} to Supabase: {e}")

    def _process_file(self, file_id):
        result = self.supabase_client.table('videos').select('filepath', 'filename').eq('id', file_id).execute()
        if not result.data:
            raise ValueError(f"No file found with id {file_id}")
        result = result.data[0]
        filepath = result['filepath']
        filename = result['filename']

        out_dir = os.path.join(self.output_folder, filename)
        os.makedirs(os.path.join(out_dir, "v0"), exist_ok=True)

        cmd = [
            "ffmpeg", "-y", "-i", filepath,
            "-preset", "veryfast", "-g", "48", "-sc_threshold", "0", "-keyint_min", "48",
            "-map", "v:0", "-map", "a:0", "-b:v:0", "3000k", "-s:v:0", "1920x1080",
            "-map", "v:0", "-map", "a:0", "-b:v:1", "1500k", "-s:v:1", "1280x720",
            "-map", "v:0", "-map", "a:0", "-b:v:2", "800k",  "-s:v:2", "854x480",
            "-map", "v:0", "-map", "a:0", "-b:v:3", "400k",  "-s:v:3", "640x360",
            "-var_stream_map", "v:0,a:0 v:1,a:1 v:2,a:2 v:3,a:3",
            "-master_pl_name", "master.m3u8",
            "-hls_time", "2", "-hls_playlist_type", "vod",
            "-hls_segment_filename", os.path.join(out_dir, "v%v", "segment_%03d.ts"),
            "-f", "hls", os.path.join(out_dir, "v%v", "prog_index.m3u8")
        ]

        try:
            self.supabase_client.table('videos').update({'status': 'processing'}).eq('id', file_id).execute()
            subprocess.run(cmd, check=True)
            self._upload_folder_to_supabase(out_dir, self.videos_bucket)
            self.supabase_client.table('videos').update({'status': 'processed', 'filepath': os.path.join(out_dir, "master.m3u8")}).eq('id', file_id).execute()
            os.remove(filepath)
            shutil.rmtree(out_dir)
        except subprocess.CalledProcessError as e:
            self.supabase_client.table('videos').update({'status': 'failed'}).eq('id', file_id).execute()
            raise RuntimeError(f"Error processing file: {e}")
