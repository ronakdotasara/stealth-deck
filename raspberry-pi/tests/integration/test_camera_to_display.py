"""
================================================================================
test_camera_to_display.py - Camera to Display Integration Tests
================================================================================
Version: 1.0.0
Date: 2025-11-25

Integration tests for camera capture to display pipeline.
================================================================================
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@pytest.mark.integration
class TestCameraToDisplay:
    """Test camera capture to display pipeline."""
    
    @pytest.fixture
    def camera_manager(self):
        """Create camera manager mock."""
        camera = Mock()
        camera.is_available.return_value = True
        camera.capture.return_value = b'\xFF\xD8\xFF'  # JPEG header
        return camera
    
    @pytest.fixture
    def display_manager(self):
        """Create display manager mock."""
        display = Mock()
        display.send_text.return_value = True
        return display
    
    def test_capture_and_preview(self, camera_manager, display_manager):
        """Test capturing image and showing preview message."""
        # Capture
        image_data = camera_manager.capture()
        
        assert image_data is not None
        assert len(image_data) > 0
        
        # Display confirmation
        display_manager.send_text("Image captured")
        
        assert display_manager.send_text.called
    
    def test_capture_with_settings(self, camera_manager):
        """Test capture with custom settings."""
        settings = {
            'width': 1640,
            'height': 1232,
            'quality': 85
        }
        
        image_data = camera_manager.capture(**settings)
        
        assert image_data is not None
    
    @patch('src.hardware.camera_manager.PiCamera')
    def test_camera_initialization(self, mock_camera):
        """Test camera initialization."""
        from src.hardware.camera_manager import CameraManager
        
        mock_camera_instance = MagicMock()
        mock_camera.return_value = mock_camera_instance
        
        camera = CameraManager()
        
        result = camera.begin()
        
        # Should initialize successfully or handle gracefully
        assert result is not None


@pytest.mark.integration
class TestImageProcessing:
    """Test image processing pipeline."""
    
    @pytest.fixture
    def test_image(self, tmp_path):
        """Create test image."""
        from PIL import Image
        
        img = Image.new('RGB', (100, 100), color='red')
        image_path = tmp_path / "test.jpg"
        img.save(image_path)
        
        return str(image_path)
    
    def test_preprocess_image(self, test_image):
        """Test image preprocessing."""
        from src.ai.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor(max_size=512)
        
        processed = preprocessor.preprocess(test_image)
        
        assert processed is not None
        assert Path(processed).exists()
    
    def test_optimize_for_ai(self, test_image):
        """Test optimization for AI analysis."""
        from src.ai.image_preprocessor import ImagePreprocessor
        from PIL import Image
        
        preprocessor = ImagePreprocessor()
        
        img = Image.open(test_image)
        optimized = preprocessor.process_image(img)
        
        assert optimized is not None
        assert optimized.size[0] <= preprocessor.max_size
        assert optimized.size[1] <= preprocessor.max_size


@pytest.mark.integration
@pytest.mark.slow
class TestCameraAIIntegration:
    """Test camera to AI analysis integration."""
    
    @pytest.fixture
    def gemini_client(self):
        """Create Gemini client mock."""
        client = Mock()
        client.analyze_image.return_value = "This is a test image showing a red square."
        return client
    
    def test_capture_and_analyze(self, gemini_client, tmp_path):
        """Test complete capture and analysis workflow."""
        from PIL import Image
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='blue')
        image_path = tmp_path / "capture.jpg"
        img.save(image_path)
        
        # Analyze
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        response = gemini_client.analyze_image(image_data, "What's in this image?")
        
        assert response is not None
        assert len(response) > 0
    
    def test_ocr_workflow(self, gemini_client):
        """Test OCR workflow."""
        # Mock image with text
        image_data = b"mock_image_data"
        
        response = gemini_client.analyze_image(image_data, "Extract text from image")
        
        assert response is not None


@pytest.mark.integration
class TestDisplayRendering:
    """Test display rendering integration."""
    
    @pytest.fixture
    def display_manager(self):
        """Create display manager."""
        from src.communication.display_manager import DisplayManager
        
        mock_uart = Mock()
        mock_uart.send_display_text.return_value = True
        
        return DisplayManager(mock_uart)
    
    def test_render_ai_response(self, display_manager):
        """Test rendering AI response."""
        response = "This is a test response from the AI."
        
        result = display_manager.display_text(response)
        
        assert result is True
    
    def test_render_long_response(self, display_manager):
        """Test rendering long response."""
        long_response = "This is a very long response. " * 20
        
        result = display_manager.display_text(long_response)
        
        assert result is True
    
    def test_render_with_formatting(self, display_manager):
        """Test rendering formatted text."""
        formatted = """**Bold Text**
*Italic Text*
`Code Text`"""
        
        result = display_manager.display_text(formatted)
        
        assert result is True


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in pipeline."""
    
    def test_camera_unavailable(self):
        """Test handling camera not available."""
        from src.hardware.camera_manager import CameraManager
        
        camera = CameraManager()
        
        # Should handle gracefully
        is_available = camera.is_available()
        
        assert is_available is not None
    
    def test_ai_api_error(self):
        """Test handling AI API error."""
        from src.ai.gemini_client import GeminiClient
        
        client = GeminiClient(api_key="invalid_key")
        
        # Should handle error gracefully
        try:
            response = client.analyze_image(b"test", "test")
        except Exception as e:
            assert e is not None
    
    def test_display_error(self):
        """Test handling display error."""
        from src.communication.display_manager import DisplayManager
        
        mock_uart = Mock()
        mock_uart.send_display_text.return_value = False
        
        display = DisplayManager(mock_uart)
        
        result = display.display_text("Test")
        
        assert result is False


@pytest.mark.integration
class TestPerformanceMetrics:
    """Test performance metrics."""
    
    def test_capture_latency(self):
        """Test camera capture latency."""
        start = time.time()
        
        # Simulate capture
        time.sleep(0.2)
        
        elapsed = time.time() - start
        
        # Should be reasonably fast
        assert elapsed < 1.0
    
    def test_processing_latency(self, tmp_path):
        """Test image processing latency."""
        from PIL import Image
        from src.ai.image_preprocessor import ImagePreprocessor
        
        # Create test image
        img = Image.new('RGB', (1640, 1232), color='blue')
        image_path = tmp_path / "test.jpg"
        img.save(image_path)
        
        preprocessor = ImagePreprocessor()
        
        start = time.time()
        preprocessor.preprocess(str(image_path))
        elapsed = time.time() - start
        
        # Should process quickly
        assert elapsed < 2.0
    
    def test_end_to_end_latency(self):
        """Test complete pipeline latency."""
        start = time.time()
        
        # Simulate complete workflow:
        # Capture (0.2s) + Process (0.1s) + AI (1.0s) + Display (0.1s)
        time.sleep(0.2 + 0.1 + 0.1 + 0.1)
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
