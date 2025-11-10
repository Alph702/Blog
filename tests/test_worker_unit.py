"""
Unit tests for worker.py module.
Tests the Worker class functionality including file saving, queuing, and processing.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import os
import uuid
import tempfile
from io import BytesIO
from datetime import datetime
from worker import Worker


class TestWorkerInitialization:
    """Test Worker class initialization."""
    
    def test_worker_init_creates_upload_folder(self):
        """Test that Worker creates the upload folder on initialization."""
        with patch('os.makedirs') as mock_makedirs, \
             patch('supabase.create_client'), \
             patch('worker.BackgroundScheduler') as mock_scheduler:
            
            mock_scheduler_instance = MagicMock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            worker = Worker(
                SUPABASE_KEY='test_key',
                SUPABASE_URL='https://test.supabase.co',
                videos_bucket='test_bucket'
            )
            
            expected_upload_dir = os.path.join(tempfile.gettempdir(), 'uploads')
            mock_makedirs.assert_called_once_with(expected_upload_dir, exist_ok=True)
            assert worker.videos_bucket == 'test_bucket'
    
    def test_worker_init_starts_scheduler(self):
        """Test that Worker starts the BackgroundScheduler on initialization."""
        with patch('os.makedirs'), \
             patch('supabase.create_client'), \
             patch('worker.BackgroundScheduler') as mock_scheduler:
            
            mock_scheduler_instance = MagicMock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            Worker(
                SUPABASE_KEY='test_key',
                SUPABASE_URL='https://test.supabase.co'
            )
            
            mock_scheduler_instance.start.assert_called_once()
    
    def test_worker_init_raises_error_without_supabase_url(self):
        """Test that Worker raises ValueError when SUPABASE_URL is missing."""
        with patch('os.makedirs'), \
             patch('worker.BackgroundScheduler'):
            
            with pytest.raises(ValueError, match="SUPABASE_URL or SUPABASE_ANON_KEY is not set"):
                Worker(SUPABASE_KEY='test_key', SUPABASE_URL=None)
    
    def test_worker_init_raises_error_without_supabase_key(self):
        """Test that Worker raises ValueError when SUPABASE_KEY is missing."""
        with patch('os.makedirs'), \
             patch('worker.BackgroundScheduler'):
            
            with pytest.raises(ValueError, match="SUPABASE_URL or SUPABASE_ANON_KEY is not set"):
                Worker(SUPABASE_KEY=None, SUPABASE_URL='https://test.supabase.co')
    
    def test_worker_init_with_default_bucket(self):
        """Test that Worker uses default bucket name when not provided."""
        with patch('os.makedirs'), \
             patch('supabase.create_client'), \
             patch('worker.BackgroundScheduler') as mock_scheduler:
            
            mock_scheduler_instance = MagicMock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            worker = Worker(
                SUPABASE_KEY='test_key',
                SUPABASE_URL='https://test.supabase.co'
            )
            
            assert worker.videos_bucket == 'video'


class TestWorkerSaveFile:
    """Test Worker.save_file method."""
    
    @pytest.fixture
    def worker(self):
        """Create a Worker instance for testing."""
        with patch('os.makedirs'), \
             patch('supabase.create_client') as mock_create_client, \
             patch('worker.BackgroundScheduler') as mock_scheduler:
            
            mock_scheduler_instance = MagicMock()
            mock_scheduler.return_value = mock_scheduler_instance
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            worker = Worker(
                SUPABASE_KEY='test_key',
                SUPABASE_URL='https://test.supabase.co',
                videos_bucket='test_videos'
            )
            return worker
    
    def test_save_file_generates_unique_filename(self, worker):
        """Test that save_file generates a unique filename with UUID."""
        mock_file = MagicMock()
        mock_file.filename = 'test_video.mp4'
        mock_file.content_type = 'video/mp4'
        mock_file.read.return_value = b'fake_video_data'
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = 'abc123def456'
            
            # Mock the storage upload and table insert
            worker.supabase_client.storage.from_().upload.return_value = None
            worker.supabase_client.table().insert().execute.return_value = None
            worker.supabase_client.table().select().eq().execute.return_value.data = [{'id': 1}]
            
            result = worker.save_file(mock_file)
            
            assert 'abc123def456.mp4' in result['filename']
    
    def test_save_file_uploads_to_supabase_storage(self, worker):
        """Test that save_file uploads the file to Supabase storage."""
        mock_file = MagicMock()
        mock_file.filename = 'test_video.mp4'
        mock_file.content_type = 'video/mp4'
        file_content = b'fake_video_data'
        mock_file.read.return_value = file_content
        
        worker.supabase_client.table().insert().execute.return_value = None
        worker.supabase_client.table().select().eq().execute.return_value.data = [{'id': 1}]
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = 'test123'
            worker.save_file(mock_file)
            
            # Verify storage upload was called
            worker.supabase_client.storage.from_.assert_called_with('test_videos')
            upload_call = worker.supabase_client.storage.from_().upload
            assert upload_call.called
    
    def test_save_file_inserts_record_in_videos_table(self, worker):
        """Test that save_file inserts a record in the videos table."""
        mock_file = MagicMock()
        mock_file.filename = 'video.mp4'
        mock_file.content_type = 'video/mp4'
        mock_file.read.return_value = b'data'
        
        worker.supabase_client.table().insert().execute.return_value = None
        worker.supabase_client.table().select().eq().execute.return_value.data = [{'id': 42}]
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = 'unique123'
            result = worker.save_file(mock_file)
            
            # Verify table insert was called
            assert worker.supabase_client.table.call_count >= 2
            assert result['file_id'] == 42
    
    def test_save_file_returns_correct_response(self, worker):
        """Test that save_file returns the expected response structure."""
        mock_file = MagicMock()
        mock_file.filename = 'my_video.mp4'
        mock_file.content_type = 'video/mp4'
        mock_file.read.return_value = b'video_bytes'
        
        worker.supabase_client.table().insert().execute.return_value = None
        worker.supabase_client.table().select().eq().execute.return_value.data = [{'id': 99}]
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = 'xyz789'
            result = worker.save_file(mock_file)
            
            assert 'message' in result
            assert 'filename' in result
            assert 'file_id' in result
            assert result['message'] == "File uploaded successfully"
            assert result['filename'] == 'xyz789.mp4'
            assert result['file_id'] == 99
    
    def test_save_file_handles_different_file_extensions(self, worker):
        """Test that save_file preserves the file extension correctly."""
        extensions = ['mp4', 'mov', 'avi', 'mkv', 'webm']
        
        for ext in extensions:
            mock_file = MagicMock()
            mock_file.filename = f'test.{ext}'
            mock_file.content_type = f'video/{ext}'
            mock_file.read.return_value = b'data'
            
            worker.supabase_client.table().insert().execute.return_value = None
            worker.supabase_client.table().select().eq().execute.return_value.data = [{'id': 1}]
            
            with patch('uuid.uuid4') as mock_uuid:
                mock_uuid.return_value.hex = 'test'
                result = worker.save_file(mock_file)
                
                assert result['filename'].endswith(f'.{ext}')


class TestWorkerQueueFile:
    """Test Worker.queue_file method."""
    
    @pytest.fixture
    def worker(self):
        """Create a Worker instance for testing."""
        with patch('os.makedirs'), \
             patch('supabase.create_client'), \
             patch('worker.BackgroundScheduler') as mock_scheduler:
            
            mock_scheduler_instance = MagicMock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            worker = Worker(
                SUPABASE_KEY='test_key',
                SUPABASE_URL='https://test.supabase.co'
            )
            return worker
    
    def test_queue_file_adds_job_to_scheduler(self, worker):
        """Test that queue_file adds a job to the scheduler."""
        file_id = 123
        
        worker.queue_file(file_id)
        
        worker.scheduler.add_job.assert_called_once()
        call_args = worker.scheduler.add_job.call_args
        
        assert call_args[1]['func'] == worker._process_file
        assert call_args[1]['trigger'] == 'date'
        assert call_args[1]['args'] == [file_id]
        assert call_args[1]['id'] == f'process_{file_id}'
    
    def test_queue_file_sets_job_parameters(self, worker):
        """Test that queue_file sets correct job parameters."""
        file_id = 456
        
        worker.queue_file(file_id)
        
        call_args = worker.scheduler.add_job.call_args
        
        assert call_args[1]['misfire_grace_time'] == 3600
        assert call_args[1]['coalesce'] is True
        assert call_args[1]['replace_existing'] is True
    
    def test_queue_file_with_different_file_ids(self, worker):
        """Test that queue_file works with different file IDs."""
        file_ids = [1, 100, 999, 5000]
        
        for file_id in file_ids:
            worker.queue_file(file_id)
            
            call_args = worker.scheduler.add_job.call_args
            assert call_args[1]['args'] == [file_id]
            assert call_args[1]['id'] == f'process_{file_id}'


class TestWorkerUploadFolderToSupabase:
    """Test Worker._upload_folder_to_supabase method."""
    
    @pytest.fixture
    def worker(self):
        """Create a Worker instance for testing."""
        with patch('os.makedirs'), \
             patch('supabase.create_client') as mock_create_client, \
             patch('worker.BackgroundScheduler') as mock_scheduler:
            
            mock_scheduler_instance = MagicMock()
            mock_scheduler.return_value = mock_scheduler_instance
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            worker = Worker(
                SUPABASE_KEY='test_key',
                SUPABASE_URL='https://test.supabase.co'
            )
            return worker
    
    def test_upload_folder_to_supabase_walks_directory(self, worker):
        """Test that _upload_folder_to_supabase walks the directory tree."""
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', create=True):
            
            mock_walk.return_value = [
                ('/test/output', [], ['file1.txt', 'file2.txt'])
            ]
            
            worker._upload_folder_to_supabase('/test/output', 'bucket')
            
            mock_walk.assert_called_once_with('/test/output')
    
    def test_upload_folder_to_supabase_uploads_files(self, worker):
        """Test that _upload_folder_to_supabase uploads each file."""
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.relpath') as mock_relpath, \
             patch('os.path.basename') as mock_basename:
            
            mock_walk.return_value = [
                ('/test/folder', [], ['video.mp4'])
            ]
            mock_relpath.return_value = 'video.mp4'
            mock_basename.return_value = 'folder'
            mock_file = MagicMock()
            mock_file.read.return_value = b'file_content'
            mock_open.return_value.__enter__.return_value = mock_file
            
            worker._upload_folder_to_supabase('/test/folder', 'test_bucket')
            
            worker.supabase_client.storage.from_.assert_called_with('test_bucket')
    
    def test_upload_folder_to_supabase_handles_errors(self, worker):
        """Test that _upload_folder_to_supabase handles upload errors gracefully."""
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.relpath') as mock_relpath, \
             patch('os.path.basename') as mock_basename, \
             patch('builtins.print') as mock_print:
            
            mock_walk.return_value = [
                ('/test', [], ['fail.mp4'])
            ]
            mock_relpath.return_value = 'fail.mp4'
            mock_basename.return_value = 'test'
            mock_file = MagicMock()
            mock_file.read.return_value = b'data'
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Simulate an upload error
            worker.supabase_client.storage.from_().upload.side_effect = Exception("Upload failed")
            
            # Should not raise exception
            worker._upload_folder_to_supabase('/test', 'bucket')
            
            # Should print error message
            assert any('Error uploading' in str(call) for call in mock_print.call_args_list)


class TestWorkerProcessFile:
    """Test Worker._process_file method."""
    
    @pytest.fixture
    def worker(self):
        """Create a Worker instance for testing."""
        with patch('os.makedirs'), \
             patch('supabase.create_client') as mock_create_client, \
             patch('worker.BackgroundScheduler') as mock_scheduler:
            
            mock_scheduler_instance = MagicMock()
            mock_scheduler.return_value = mock_scheduler_instance
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            worker = Worker(
                SUPABASE_KEY='test_key',
                SUPABASE_URL='https://test.supabase.co',
                videos_bucket='test_bucket'
            )
            return worker
    
    def test_process_file_raises_error_if_file_not_found(self, worker):
        """Test that _process_file raises ValueError if file_id doesn't exist."""
        worker.supabase_client.table().select().eq().execute.return_value.data = []
        
        with pytest.raises(ValueError, match="No file found with id 999"):
            worker._process_file(999)
    
    def test_process_file_downloads_video_from_storage(self, worker):
        """Test that _process_file downloads the video from Supabase storage."""
        file_id = 1
        worker.supabase_client.table().select().eq().execute.return_value.data = [{
            'filepath': 'https://test.supabase.co/storage/v1/object/public/test_bucket/upload/video.mp4',
            'filename': 'video.mp4'
        }]
        worker.supabase_client.storage.from_().download.return_value = b'video_data'
        
        with patch('builtins.open', create=True), \
             patch('requests.post') as mock_post:
            
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {'master_playlist': 'https://example.com/master.m3u8'}
            
            worker._process_file(file_id)
            
            worker.supabase_client.storage.from_.assert_called_with('test_bucket')
            worker.supabase_client.storage.from_().download.assert_called_once()
    
    def test_process_file_updates_status_to_processing(self, worker):
        """Test that _process_file updates video status to 'processing'."""
        file_id = 2
        worker.supabase_client.table().select().eq().execute.return_value.data = [{
            'filepath': 'https://test.com/video.mp4',
            'filename': 'video.mp4'
        }]
        worker.supabase_client.storage.from_().download.return_value = b'data'
        
        with patch('builtins.open', create=True), \
             patch('requests.post') as mock_post:
            
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {'master_playlist': 'https://example.com/master.m3u8'}
            
            worker._process_file(file_id)
            
            # Check that status was updated to processing
            update_calls = [call for call in worker.supabase_client.table().update.call_args_list]
            assert any('processing' in str(call) for call in update_calls)
    
    def test_process_file_sends_to_ffmpeg_service(self, worker):
        """Test that _process_file sends video to FFmpeg service."""
        file_id = 3
        worker.supabase_client.table().select().eq().execute.return_value.data = [{
            'filepath': 'https://test.com/video.mp4',
            'filename': 'test.mp4'
        }]
        worker.supabase_client.storage.from_().download.return_value = b'video_bytes'
        
        with patch('builtins.open', create=True), \
             patch('requests.post') as mock_post:
            
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {'master_playlist': 'https://cdn.com/output.m3u8'}
            
            worker._process_file(file_id)
            
            mock_post.assert_called_once()
            assert 'https://ffmpeg.pythonanywhere.com/upload/' in mock_post.call_args[0][0]
    
    def test_process_file_updates_status_to_processed_on_success(self, worker):
        """Test that _process_file updates status to 'processed' on success."""
        file_id = 4
        master_playlist_url = 'https://cdn.example.com/videos/output/master.m3u8'
        
        worker.supabase_client.table().select().eq().execute.return_value.data = [{
            'filepath': 'https://test.com/video.mp4',
            'filename': 'video.mp4'
        }]
        worker.supabase_client.storage.from_().download.return_value = b'data'
        
        with patch('builtins.open', create=True), \
             patch('requests.post') as mock_post:
            
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {'master_playlist': master_playlist_url}
            
            worker._process_file(file_id)
            
            # Verify status update to processed
            update_calls = worker.supabase_client.table().update.call_args_list
            # Look for the final update call with processed status
            final_update = update_calls[-2]  # Second to last call (before remove)
            assert 'processed' in str(final_update)
    
    def test_process_file_removes_original_from_storage(self, worker):
        """Test that _process_file removes the original file from storage after processing."""
        file_id = 5
        filename = 'original.mp4'
        
        worker.supabase_client.table().select().eq().execute.return_value.data = [{
            'filepath': f'https://test.com/{filename}',
            'filename': filename
        }]
        worker.supabase_client.storage.from_().download.return_value = b'data'
        
        with patch('builtins.open', create=True), \
             patch('requests.post') as mock_post:
            
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {'master_playlist': 'https://cdn.com/master.m3u8'}
            
            worker._process_file(file_id)
            
            # Verify file removal
            worker.supabase_client.storage.from_().remove.assert_called_once()
    
    def test_process_file_updates_status_to_failed_on_error(self, worker):
        """Test that _process_file updates status to 'failed' on processing error."""
        file_id = 6
        
        worker.supabase_client.table().select().eq().execute.return_value.data = [{
            'filepath': 'https://test.com/video.mp4',
            'filename': 'video.mp4'
        }]
        worker.supabase_client.storage.from_().download.return_value = b'data'
        
        with patch('builtins.open', create=True), \
             patch('requests.post') as mock_post:
            
            # Simulate FFmpeg service error
            mock_post.side_effect = Exception("FFmpeg processing failed")
            
            with pytest.raises(RuntimeError, match="Error processing file"):
                worker._process_file(file_id)
            
            # Verify status was updated to failed
            update_calls = worker.supabase_client.table().update.call_args_list
            assert any('failed' in str(call) for call in update_calls)
    
    def test_process_file_with_timeout(self, worker):
        """Test that _process_file respects the timeout parameter."""
        file_id = 7
        
        worker.supabase_client.table().select().eq().execute.return_value.data = [{
            'filepath': 'https://test.com/video.mp4',
            'filename': 'video.mp4'
        }]
        worker.supabase_client.storage.from_().download.return_value = b'data'
        
        with patch('builtins.open', create=True), \
             patch('requests.post') as mock_post:
            
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {'master_playlist': 'https://cdn.com/master.m3u8'}
            
            worker._process_file(file_id)
            
            # Verify timeout was set in the request
            assert mock_post.call_args[1]['timeout'] == 3000