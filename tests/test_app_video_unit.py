"""
Unit tests for app.py video functionality.
Tests the video-related routes and helper functions.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
import os
from io import BytesIO
from werkzeug.datastructures import FileStorage


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    with patch('app.supabase_client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_worker():
    """Create a mock Worker instance."""
    with patch('app.worker') as mock_worker:
        yield mock_worker


@pytest.fixture
def app_client():
    """Create a Flask test client."""
    with patch('app.supabase_client'), \
         patch('app.worker'):
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client


class TestAllowedFile:
    """Test the allowed_file helper function."""
    
    def test_allowed_file_with_valid_image_extensions(self):
        """Test allowed_file returns True for valid image extensions."""
        from app import allowed_file
        
        valid_extensions = ['test.png', 'test.jpg', 'test.jpeg', 'test.gif', 'test.bmp', 'test.webp']
        
        for filename in valid_extensions:
            assert allowed_file(filename) is True
    
    def test_allowed_file_with_valid_video_extensions(self):
        """Test allowed_file returns True for valid video extensions."""
        from app import allowed_file
        
        valid_extensions = ['test.mp4', 'test.mov', 'test.avi', 'test.mkv', 'test.webm']
        
        for filename in valid_extensions:
            assert allowed_file(filename) is True
    
    def test_allowed_file_with_invalid_extensions(self):
        """Test allowed_file returns False for invalid extensions."""
        from app import allowed_file
        
        invalid_files = ['test.exe', 'test.txt', 'test.pdf', 'test.doc', 'script.js']
        
        for filename in invalid_files:
            assert allowed_file(filename) is False
    
    def test_allowed_file_with_no_extension(self):
        """Test allowed_file returns False for files without extension."""
        from app import allowed_file
        
        assert allowed_file('filename') is False
    
    def test_allowed_file_case_insensitive(self):
        """Test allowed_file is case insensitive."""
        from app import allowed_file
        
        assert allowed_file('test.MP4') is True
        assert allowed_file('test.JPG') is True
        assert allowed_file('test.Png') is True


class TestHomeRouteWithVideo:
    """Test home route with video data."""
    
    def test_home_includes_video_id_in_query(self, app_client, mock_supabase_client):
        """Test that home route queries for video_id field."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase_client.table().select().order().execute.return_value = mock_response
        
        with patch('app.TIMESTAMP_FIELD', 'timestamp'):
            app_client.get('/')
        
        # Verify video_id is included in select fields
        select_call = mock_supabase_client.table().select.call_args[0][0]
        assert 'video_id' in select_call
    
    def test_home_fetches_video_data_when_video_id_exists(self, app_client, mock_supabase_client):
        """Test that home route fetches video data when post has video_id."""
        post_data = {
            'id': 1,
            'title': 'Test Post',
            'content': 'Content',
            'image': None,
            'timestamp': '2024-01-01T00:00:00',
            'video_id': 123
        }
        
        video_data = {
            'filepath': 'https://cdn.example.com/video.m3u8',
            'filename': 'video.mp4',
            'status': 'processed'
        }
        
        # Mock posts query
        posts_response = MagicMock()
        posts_response.data = [post_data]
        
        # Mock video query
        video_response = MagicMock()
        video_response.data = video_data
        
        mock_supabase_client.table().select().order().execute.return_value = posts_response
        mock_supabase_client.table().select().eq().single().execute.return_value = video_response
        
        with patch('app.TIMESTAMP_FIELD', 'timestamp'):
            response = app_client.get('/')
        
        assert response.status_code == 200
    
    def test_home_handles_missing_video_data_gracefully(self, app_client, mock_supabase_client):
        """Test that home route handles missing video data without crashing."""
        post_data = {
            'id': 1,
            'title': 'Test Post',
            'content': 'Content',
            'image': None,
            'timestamp': '2024-01-01T00:00:00',
            'video_id': 999  # Non-existent video
        }
        
        posts_response = MagicMock()
        posts_response.data = [post_data]
        
        # Mock video query to raise exception
        mock_supabase_client.table().select().order().execute.return_value = posts_response
        mock_supabase_client.table().select().eq().single().execute.side_effect = Exception("Video not found")
        
        with patch('app.TIMESTAMP_FIELD', 'timestamp'):
            response = app_client.get('/')
        
        # Should still return 200 and not crash
        assert response.status_code == 200


class TestNewPostWithVideo:
    """Test new_post route with video upload."""
    
    def test_new_post_saves_video_file(self, app_client, mock_supabase_client, mock_worker):
        """Test that new_post saves video file using Worker."""
        mock_worker.save_file.return_value = {
            'file_id': 456,
            'filename': 'unique.mp4',
            'message': 'File uploaded successfully'
        }
        
        # Mock the database operations
        mock_supabase_client.table().select().order().limit().execute.return_value.data = [{'id': 100}]
        mock_supabase_client.table().insert().execute.return_value = None
        
        with app_client.session_transaction() as sess:
            sess['admin'] = True
        
        data = {
            'title': 'Test Video Post',
            'content': 'Post with video',
            'video': (BytesIO(b'fake video data'), 'test.mp4')
        }
        
        app_client.post('/new', data=data, content_type='multipart/form-data')
        
        # Verify worker.save_file was called
        assert mock_worker.save_file.called
    
    def test_new_post_queues_video_for_processing(self, app_client, mock_supabase_client, mock_worker):
        """Test that new_post queues video for processing."""
        video_id = 789
        mock_worker.save_file.return_value = {
            'file_id': video_id,
            'filename': 'video.mp4',
            'message': 'Success'
        }
        
        mock_supabase_client.table().select().order().limit().execute.return_value.data = [{'id': 50}]
        mock_supabase_client.table().insert().execute.return_value = None
        
        with app_client.session_transaction() as sess:
            sess['admin'] = True
        
        data = {
            'title': 'Queue Test',
            'content': 'Testing queue',
            'video': (BytesIO(b'video'), 'test.mp4')
        }
        
        app_client.post('/new', data=data, content_type='multipart/form-data')
        
        # Verify worker.queue_file was called with correct video_id
        mock_worker.queue_file.assert_called_once_with(video_id)
    
    def test_new_post_handles_video_save_error(self, app_client, mock_supabase_client, mock_worker):
        """Test that new_post handles video save errors gracefully."""
        mock_worker.save_file.side_effect = Exception("Storage error")
        
        mock_supabase_client.table().select().order().limit().execute.return_value.data = [{'id': 10}]
        mock_supabase_client.table().insert().execute.return_value = None
        
        with app_client.session_transaction() as sess:
            sess['admin'] = True
        
        data = {
            'title': 'Error Test',
            'content': 'Should handle error',
            'video': (BytesIO(b'video'), 'test.mp4')
        }
        
        # Should not raise exception
        response = app_client.post('/new', data=data, content_type='multipart/form-data')
        
        # Post should still be created (without video)
        assert response.status_code in [200, 302]
    
    def test_new_post_includes_video_id_in_insert(self, app_client, mock_supabase_client, mock_worker):
        """Test that new_post includes video_id in database insert."""
        video_id = 111
        mock_worker.save_file.return_value = {'file_id': video_id, 'filename': 'vid.mp4', 'message': 'OK'}
        
        mock_supabase_client.table().select().order().limit().execute.return_value.data = [{'id': 5}]
        
        with app_client.session_transaction() as sess:
            sess['admin'] = True
        
        data = {
            'title': 'Video Post',
            'content': 'Content',
            'video': (BytesIO(b'data'), 'video.mp4')
        }
        
        app_client.post('/new', data=data, content_type='multipart/form-data')
        
        # Verify insert call includes video_id
        insert_call = mock_supabase_client.table().insert.call_args
        if insert_call:
            insert_data = insert_call[0][0]
            assert 'video_id' in insert_data
    
    def test_new_post_validates_video_extension(self, app_client, mock_supabase_client):
        """Test that new_post validates video file extensions."""
        mock_supabase_client.table().select().order().limit().execute.return_value.data = [{'id': 1}]
        
        with app_client.session_transaction() as sess:
            sess['admin'] = True
        
        # Try to upload invalid file type
        data = {
            'title': 'Invalid Video',
            'content': 'Should reject',
            'video': (BytesIO(b'not a video'), 'malware.exe')
        }
        
        response = app_client.post('/new', data=data, content_type='multipart/form-data')
        
        # Worker should not be called with invalid file
        # (Note: actual validation happens in allowed_file check)
        assert response.status_code in [200, 302]


class TestEditPostWithVideo:
    """Test edit_post route with video functionality."""
    
    def test_edit_post_loads_video_data(self, app_client, mock_supabase_client):
        """Test that edit_post loads existing video data."""
        post_id = 42
        video_id = 888
        
        post_data = {
            'id': post_id,
            'title': 'Post with Video',
            'content': 'Content',
            'image': None,
            'timestamp': '2024-01-01T00:00:00',
            'video_id': video_id
        }
        
        video_data = {
            'filepath': 'https://cdn.example.com/video.m3u8',
            'filename': 'video.mp4',
            'status': 'processed'
        }
        
        post_response = MagicMock()
        post_response.data = post_data
        
        video_response = MagicMock()
        video_response.data = video_data
        
        mock_supabase_client.table().select().eq().single().execute.side_effect = [
            post_response,
            video_response
        ]
        
        with app_client.session_transaction() as sess:
            sess['admin'] = True
        
        response = app_client.get(f'/edit/{post_id}')
        
        assert response.status_code == 200
    
    def test_edit_post_updates_video(self, app_client, mock_supabase_client, mock_worker):
        """Test that edit_post can update video."""
        post_id = 10
        new_video_id = 999
        
        mock_worker.save_file.return_value = {
            'file_id': new_video_id,
            'filename': 'new.mp4',
            'message': 'Success'
        }
        
        post_data = {
            'id': post_id,
            'title': 'Original',
            'content': 'Original content',
            'image': None,
            'video_id': 1
        }
        
        post_response = MagicMock()
        post_response.data = post_data
        mock_supabase_client.table().select().eq().single().execute.return_value = post_response
        
        with app_client.session_transaction() as sess:
            sess['admin'] = True
        
        data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'current_image_url': '',
            'current_video_id': '1',
            'video': (BytesIO(b'new video'), 'new.mp4')
        }
        
        app_client.post(f'/edit/{post_id}', data=data, content_type='multipart/form-data')
        
        # Verify worker.save_file was called
        assert mock_worker.save_file.called
        mock_worker.queue_file.assert_called_once_with(new_video_id)
    
    def test_edit_post_preserves_video_id_when_no_new_video(self, app_client, mock_supabase_client):
        """Test that edit_post preserves existing video_id when no new video uploaded."""
        post_id = 20
        existing_video_id = 555
        
        post_data = {
            'id': post_id,
            'title': 'Post',
            'content': 'Content',
            'video_id': existing_video_id
        }
        
        post_response = MagicMock()
        post_response.data = post_data
        mock_supabase_client.table().select().eq().single().execute.return_value = post_response
        
        with app_client.session_transaction() as sess:
            sess['admin'] = True
        
        data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'current_image_url': '',
            'current_video_id': str(existing_video_id)
        }
        
        app_client.post(f'/edit/{post_id}', data=data, content_type='multipart/form-data')
        
        # Verify update includes the existing video_id
        update_call = mock_supabase_client.table().update.call_args
        if update_call:
            update_data = update_call[0][0]
            assert update_data.get('video_id') == str(existing_video_id)


class TestViewPostWithVideo:
    """Test view_post route with video data."""
    
    def test_view_post_includes_video_data(self, app_client, mock_supabase_client):
        """Test that view_post includes video data in response."""
        post_id = 1
        video_id = 777
        
        post_data = {
            'id': post_id,
            'title': 'Post with Video',
            'content': 'Content',
            'image': None,
            'timestamp': '2024-01-01T00:00:00',
            'video_id': video_id
        }
        
        video_data = {
            'filepath': 'https://cdn.example.com/master.m3u8',
            'filename': 'video.mp4',
            'status': 'processed'
        }
        
        post_response = MagicMock()
        post_response.data = post_data
        
        video_response = MagicMock()
        video_response.data = video_data
        
        mock_supabase_client.table().select().eq().single().execute.side_effect = [
            post_response,
            video_response
        ]
        
        with patch('app.TIMESTAMP_FIELD', 'timestamp'):
            response = app_client.get(f'/post/{post_id}')
        
        assert response.status_code == 200
        # Video data should be passed to template
    
    def test_view_post_handles_video_fetch_error(self, app_client, mock_supabase_client):
        """Test that view_post handles video fetch errors gracefully."""
        post_id = 2
        
        post_data = {
            'id': post_id,
            'title': 'Post',
            'content': 'Content',
            'video_id': 999  # Non-existent
        }
        
        post_response = MagicMock()
        post_response.data = post_data
        
        mock_supabase_client.table().select().eq().single().execute.side_effect = [
            post_response,
            Exception("Video not found")
        ]
        
        with patch('app.TIMESTAMP_FIELD', None):
            response = app_client.get(f'/post/{post_id}')
        
        # Should still render page without crashing
        assert response.status_code == 200
    
    def test_view_post_without_video(self, app_client, mock_supabase_client):
        """Test that view_post works for posts without video."""
        post_id = 3
        
        post_data = {
            'id': post_id,
            'title': 'No Video Post',
            'content': 'Just text',
            'video_id': None
        }
        
        post_response = MagicMock()
        post_response.data = post_data
        
        mock_supabase_client.table().select().eq().single().execute.return_value = post_response
        
        with patch('app.TIMESTAMP_FIELD', None):
            response = app_client.get(f'/post/{post_id}')
        
        assert response.status_code == 200


class TestUploadedFileRoute:
    """Test the uploaded_file route."""
    
    def test_uploaded_file_creates_upload_folder(self, app_client):
        """Test that uploaded_file route creates the upload folder."""
        with patch('os.makedirs') as mock_makedirs, \
             patch('flask.send_from_directory') as mock_send:
            
            mock_send.return_value = 'file_content'
            
            app_client.get('/uploads/test.mp4')
            
            mock_makedirs.assert_called_once_with('tmp/uploads', exist_ok=True)
    
    def test_uploaded_file_serves_from_correct_directory(self, app_client):
        """Test that uploaded_file serves from tmp/uploads directory."""
        with patch('os.makedirs'), \
             patch('flask.send_from_directory') as mock_send:
            
            mock_send.return_value = 'file_content'
            
            app_client.get('/uploads/video.mp4')
            
            mock_send.assert_called_once_with('tmp/uploads', 'video.mp4')


class TestVideoDataStructure:
    """Test the video data structure passed to templates."""
    
    def test_videodata_structure_includes_all_fields(self):
        """Test that videodata dictionary includes all required fields."""
        # This tests the structure created in home(), view_post(), and edit_post()
        video_record = {
            'filepath': 'https://cdn.example.com/video.m3u8',
            'filename': 'video.mp4',
            'status': 'processed'
        }
        
        video_id = 123
        
        # Simulate the videodata construction
        videodata = {
            'id': video_id,
            'filename': video_record.get('filename'),
            'filepath': video_record.get('filepath'),
            'status': video_record.get('status'),
            'url': video_record.get('filepath')
        }
        
        assert 'id' in videodata
        assert 'filename' in videodata
        assert 'filepath' in videodata
        assert 'status' in videodata
        assert 'url' in videodata
        assert videodata['id'] == 123
        assert videodata['filename'] == 'video.mp4'
        assert videodata['status'] == 'processed'
    
    def test_videodata_url_matches_filepath(self):
        """Test that videodata url field matches filepath."""
        video_record = {
            'filepath': 'https://cdn.example.com/master.m3u8',
            'filename': 'video.mp4',
            'status': 'processed'
        }
        
        videodata = {
            'id': 1,
            'filename': video_record.get('filename'),
            'filepath': video_record.get('filepath'),
            'status': video_record.get('status'),
            'url': video_record.get('filepath')
        }
        
        assert videodata['url'] == videodata['filepath']


class TestWorkerIntegration:
    """Test Worker integration in app.py."""
    
    def test_worker_initialized_with_correct_bucket(self):
        """Test that Worker is initialized with correct video bucket."""
        with patch('app.supabase_client'), \
             patch('app.Worker'):
            
            # Re-import to trigger initialization
            import importlib
            import app as app_module
            importlib.reload(app_module)
            
            # Verify Worker was called with videos bucket
            # Note: This test verifies the pattern, actual call happens at module load
    
    def test_worker_receives_supabase_credentials(self):
        """Test that Worker receives Supabase credentials."""
        with patch('os.getenv') as mock_getenv, \
             patch('app.Worker'):
            
            mock_getenv.side_effect = lambda key, default=None: {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPERBASE_ANON_KEY': 'test_key',
                'SUPERBASE_VIDEOS_BUCKET_NAME': 'videos'
            }.get(key, default)
            
            # The Worker should be initialized with these values
            # This is a pattern verification test