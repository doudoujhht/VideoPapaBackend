# Running Unit Tests

This directory contains unit tests for the VideoPapa backend API endpoints.

## Setup

1. Install test dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the tests:
   ```bash
   pytest test_main.py -v
   ```

   Or with Python 3:
   ```bash
   python3 -m pytest test_main.py -v
   ```

## Test Coverage

The test suite includes the following test cases:

### `create_video` endpoint tests:
1. **test_create_video_success** - Verifies that the endpoint successfully creates an MP4 video from valid image and audio inputs
2. **test_create_video_saves_files_to_output_dir** - Verifies that uploaded files are correctly saved to the output directory
3. **test_create_video_returns_valid_video_url** - Verifies that the endpoint returns a valid video URL in the response

### `download_video` endpoint tests:
4. **test_download_video_success** - Verifies that the endpoint successfully serves an existing video file
5. **test_download_video_non_existent_file** - Verifies that the endpoint handles requests for non-existent files appropriately

### Additional security test:
- **test_download_video_with_special_characters** - Verifies that the endpoint handles path traversal attempts safely

## Test Approach

The tests use:
- **pytest** as the testing framework
- **FastAPI TestClient** for making API requests
- **unittest.mock** for mocking subprocess calls (ffmpeg) and file operations
- Temporary files and directories to avoid side effects

All tests are isolated and use mocks to avoid actually running ffmpeg or creating real video files during testing.
