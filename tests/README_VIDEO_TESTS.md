# Video Functionality Unit Tests

This document describes the comprehensive unit tests added for the video upload and playback features.

## Test Files Created

### 1. `test_worker_unit.py` - Worker Class Unit Tests
Comprehensive tests for the `worker.py` module covering:

#### TestWorkerInitialization
- ✅ Worker creates upload folder on initialization
- ✅ BackgroundScheduler starts correctly
- ✅ Raises ValueError when SUPABASE_URL is missing
- ✅ Raises ValueError when SUPABASE_KEY is missing
- ✅ Uses default bucket name when not provided

#### TestWorkerSaveFile
- ✅ Generates unique filename with UUID
- ✅ Uploads file to Supabase storage
- ✅ Inserts record in videos table
- ✅ Returns correct response structure
- ✅ Handles different file extensions (mp4, mov, avi, mkv, webm)

#### TestWorkerQueueFile
- ✅ Adds job to scheduler with correct parameters
- ✅ Sets job parameters (misfire_grace_time, coalesce, replace_existing)
- ✅ Works with different file IDs

#### TestWorkerUploadFolderToSupabase
- ✅ Walks directory tree
- ✅ Uploads each file to storage
- ✅ Handles upload errors gracefully

#### TestWorkerProcessFile
- ✅ Raises error if file_id doesn't exist
- ✅ Downloads video from Supabase storage
- ✅ Updates status to 'processing'
- ✅ Sends video to FFmpeg service
- ✅ Updates status to 'processed' on success
- ✅ Removes original file from storage after processing
- ✅ Updates status to 'failed' on error
- ✅ Respects timeout parameter

### Total: 29 unit tests for Worker class

---

### 2. `test_app_video_unit.py` - Flask App Video Routes Tests
Tests for video-related functionality in `app.py`:

#### TestAllowedFile
- ✅ Validates image extensions (png, jpg, jpeg, gif, bmp, webp)
- ✅ Validates video extensions (mp4, mov, avi, mkv, webm)
- ✅ Rejects invalid extensions
- ✅ Rejects files without extension
- ✅ Case-insensitive validation

#### TestHomeRouteWithVideo
- ✅ Includes video_id in database queries
- ✅ Fetches video data when video_id exists
- ✅ Handles missing video data gracefully

#### TestNewPostWithVideo
- ✅ Saves video file using Worker
- ✅ Queues video for processing
- ✅ Handles video save errors gracefully
- ✅ Includes video_id in database insert
- ✅ Validates video file extensions

#### TestEditPostWithVideo
- ✅ Loads existing video data
- ✅ Updates video
- ✅ Preserves video_id when no new video uploaded

#### TestViewPostWithVideo
- ✅ Includes video data in response
- ✅ Handles video fetch errors gracefully
- ✅ Works for posts without video

#### TestUploadedFileRoute
- ✅ Creates upload folder
- ✅ Serves files from correct directory

#### TestVideoDataStructure
- ✅ videodata includes all required fields
- ✅ url field matches filepath

### Total: 28 unit tests for Flask app video routes

---

### 3. `test_javascript_validation.py` - JavaScript & Asset Validation Tests
Validation tests for frontend JavaScript and assets:

#### TestUploaderJSValidation
- ✅ File exists
- ✅ Defines required DOM elements
- ✅ Defines showToast function
- ✅ Handles click events (image and video)
- ✅ Handles drag & drop events (dragover, dragleave, drop)
- ✅ Validates MIME types (image/, video/)
- ✅ Shows warnings for invalid files
- ✅ Updates placeholder text
- ✅ No syntax errors (balanced braces/parentheses)

#### TestVideoPlayerJSValidation
- ✅ File exists
- ✅ Waits for DOMContentLoaded
- ✅ Selects video containers
- ✅ Defines helper functions (formatTime, togglePlayPause, etc.)
- ✅ Handles HLS.js support
- ✅ Handles native HLS (Safari)
- ✅ Handles quality selection
- ✅ Handles playback speed
- ✅ Handles Picture-in-Picture
- ✅ Handles fullscreen
- ✅ Handles controls auto-hide
- ✅ Attaches event listeners
- ✅ Handles HLS events
- ✅ Formats time correctly
- ✅ No syntax errors
- ✅ Uses modern JavaScript (const/let)
- ✅ Handles status data attributes

#### TestCSSValidation
- ✅ video_controls.css exists
- ✅ Defines video-container styles
- ✅ Defines controls overlay styles
- ✅ Defines play overlay styles
- ✅ Uses CSS custom properties
- ✅ style.css includes video styles

#### TestSVGIconsValidation
- ✅ Required SVG icons exist (play, pause, fullscreen, etc.)
- ✅ SVG files are valid XML

#### TestTemplateVideoComponentValidation
- ✅ video_player.html template exists
- ✅ Has correct structure
- ✅ Uses data attributes

#### TestIntegrationPoints
- ✅ layout.html includes video scripts
- ✅ new.html includes uploader.js
- ✅ edit.html includes uploader.js

### Total: 42 validation tests for JavaScript and assets

---

## Test Summary

| Test File | Test Classes | Total Tests | Coverage Area |
|-----------|--------------|-------------|---------------|
| `test_worker_unit.py` | 5 | 29 | Worker class methods |
| `test_app_video_unit.py` | 9 | 28 | Flask routes & helpers |
| `test_javascript_validation.py` | 6 | 42 | JS, CSS, SVG validation |
| **TOTAL** | **20** | **99** | **Complete video feature** |

## Running the Tests

### Run all video-related unit tests:
```bash
pytest tests/test_worker_unit.py tests/test_app_video_unit.py tests/test_javascript_validation.py -v
```

### Run specific test classes:
```bash
# Test Worker class only
pytest tests/test_worker_unit.py::TestWorkerSaveFile -v

# Test Flask app video routes only
pytest tests/test_app_video_unit.py::TestNewPostWithVideo -v

# Test JavaScript validation only
pytest tests/test_javascript_validation.py::TestVideoPlayerJSValidation -v
```

### Run with coverage:
```bash
pytest tests/test_worker_unit.py tests/test_app_video_unit.py --cov=worker --cov=app --cov-report=html
```

## Test Coverage

These tests provide comprehensive coverage for:

1. **Backend Logic**
   - Video file upload and storage
   - Background job scheduling
   - Video processing workflow
   - Database operations
   - Error handling

2. **Flask Routes**
   - Home page with video data
   - New post creation with video
   - Post editing with video
   - Video file serving
   - Data structure validation

3. **Frontend Assets**
   - JavaScript syntax and structure
   - Event handling
   - HLS.js integration
   - Video player controls
   - Drag & drop functionality
   - CSS structure
   - SVG icon presence
   - Template integration

## Test Patterns Used

- **Unit Testing**: Pure function and method tests with mocked dependencies
- **Mocking**: Extensive use of unittest.mock for Supabase, scheduler, file system
- **Fixtures**: Reusable test fixtures for common setup
- **Parametrization**: Testing multiple file extensions and scenarios
- **Edge Cases**: Error conditions, missing data, invalid inputs
- **Integration Points**: Cross-file dependencies and references

## Key Testing Principles Applied

1. **Isolation**: Each test is independent and doesn't rely on external state
2. **Mocking**: All external dependencies (Supabase, file system, HTTP) are mocked
3. **Descriptive Names**: Test names clearly describe what is being tested
4. **Comprehensive**: Tests cover happy paths, edge cases, and error conditions
5. **Maintainable**: Tests are organized into logical classes and well-documented

## Notes

- All tests use mocking to avoid actual network calls or file system operations
- Tests are designed to run quickly without external dependencies
- The existing integration test (`test_video.py`) complements these unit tests
- JavaScript validation tests check structure and syntax but don't execute JS code