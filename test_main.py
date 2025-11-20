import os
import pytest
import tempfile
import shutil
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from io import BytesIO
from server import app, OUTPUT_DIR


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for tests."""
    temp_dir = tempfile.mkdtemp()
    original_output_dir = OUTPUT_DIR
    
    # Patch the OUTPUT_DIR in the main module
    with patch('main.OUTPUT_DIR', temp_dir):
        yield temp_dir
    
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_image_file():
    """Create a mock image file for testing."""
    # Create a simple PNG file (1x1 pixel)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return BytesIO(png_data)


@pytest.fixture
def mock_audio_file():
    """Create a mock audio file for testing."""
    # Create a minimal valid MP3 header
    mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 100
    return BytesIO(mp3_data)


class TestCreateVideo:
    """Test cases for the create_video endpoint."""
    
    def test_create_video_success(self, client):
        """Test 1: create_video endpoint successfully creates an MP4 video from valid image and audio inputs."""
        # Create mock files
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        audio_content = b'\xff\xfb\x90\x00' + b'\x00' * 100
        
        # Mock subprocess.run to avoid actually running ffmpeg
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Mock uuid to have predictable filenames
            with patch('main.uuid.uuid4') as mock_uuid:
                mock_uuid.side_effect = ['img-uuid', 'audio-uuid', 'video-uuid']
                
                # Send POST request
                response = client.post(
                    "/create-video",
                    files={
                        "image": ("test_image.png", image_content, "image/png"),
                        "audio": ("test_audio.mp3", audio_content, "audio/mp3")
                    }
                )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "video_url" in data
        assert data["video_url"] == "/download/video-uuid.mp4"
        
        # Verify subprocess was called with correct ffmpeg command
        mock_run.assert_called_once()
        ffmpeg_cmd = mock_run.call_args[0][0]
        assert ffmpeg_cmd[0] == "ffmpeg"
        assert "-i" in ffmpeg_cmd
        assert "videos/video-uuid.mp4" in ffmpeg_cmd
    
    def test_create_video_saves_files_to_output_dir(self, client):
        """Test 2: create_video endpoint correctly saves uploaded image and audio files to the specified output directory."""
        image_content = b'\x89PNG\r\n\x1a\n'
        audio_content = b'\xff\xfb\x90\x00'
        
        # Track which files were created
        created_files = []
        original_open = open
        
        def track_file_creation(path, mode, *args, **kwargs):
            if mode == "wb" and OUTPUT_DIR in path:
                created_files.append(path)
            return original_open(path, mode, *args, **kwargs)
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.open', side_effect=track_file_creation) as mock_open:
                with patch('main.uuid.uuid4') as mock_uuid:
                    mock_uuid.side_effect = ['img-123', 'audio-456', 'video-789']
                    
                    response = client.post(
                        "/create-video",
                        files={
                            "image": ("image.jpg", image_content, "image/jpeg"),
                            "audio": ("audio.mp3", audio_content, "audio/mp3")
                        }
                    )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify files were saved to OUTPUT_DIR
        assert any(f"{OUTPUT_DIR}/img-123.jpg" in f for f in created_files)
        assert any(f"{OUTPUT_DIR}/audio-456.mp3" in f for f in created_files)
    
    def test_create_video_returns_valid_video_url(self, client):
        """Test 3: create_video endpoint returns a valid video URL in the response."""
        image_content = b'fake_image_data'
        audio_content = b'fake_audio_data'
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('main.uuid.uuid4') as mock_uuid:
                mock_uuid.side_effect = ['uuid1', 'uuid2', 'output-video-uuid']
                
                response = client.post(
                    "/create-video",
                    files={
                        "image": ("test.png", image_content, "image/png"),
                        "audio": ("test.mp3", audio_content, "audio/mp3")
                    }
                )
        
        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        
        # Verify video_url field exists and has correct format
        assert "video_url" in data
        assert isinstance(data["video_url"], str)
        assert data["video_url"].startswith("/download/")
        assert data["video_url"].endswith(".mp4")
        assert data["video_url"] == "/download/output-video-uuid.mp4"


class TestDownloadVideo:
    """Test cases for the download_video endpoint."""
    
    def test_download_video_success(self, client):
        """Test 4: download_video endpoint successfully serves an existing video file."""
        # Create a temporary video file
        test_filename = "test_video.mp4"
        test_file_path = os.path.join(OUTPUT_DIR, test_filename)
        test_content = b"fake video content"
        
        # Ensure OUTPUT_DIR exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        try:
            # Create test file
            with open(test_file_path, "wb") as f:
                f.write(test_content)
            
            # Request the video
            response = client.get(f"/download/{test_filename}")
            
            # Assertions
            assert response.status_code == 200
            assert response.content == test_content
            assert response.headers["content-type"] == "video/mp4"
        finally:
            # Cleanup
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    def test_download_video_non_existent_file(self, client):
        """Test 5: download_video endpoint handles requests for non-existent files appropriately."""
        # Request a non-existent video
        non_existent_filename = "non_existent_video_12345.mp4"
        response = client.get(f"/download/{non_existent_filename}")
        
        # The endpoint should return a 404 or 500 error
        # FastAPI's FileResponse will raise an error if file doesn't exist
        assert response.status_code in [404, 500]
    
    def test_download_video_with_special_characters(self, client):
        """Additional test: Verify the endpoint handles filenames safely."""
        # Try to access a file with path traversal attempt
        malicious_filename = "../../../etc/passwd"
        response = client.get(f"/download/{malicious_filename}")
        
        # Should not allow path traversal
        assert response.status_code in [404, 500]
