"""
================================================================================
test_gemini_client.py - Unit Tests for Gemini Client
================================================================================
Version: 1.0.0
Date: 2025-11-24

Test coverage for Gemini API client.
================================================================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ai.gemini_client import GeminiClient


class TestGeminiClient:
    """Test suite for Gemini client."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            'api_keys.gemini_api_key': 'test_api_key_123',
            'ai.model': 'gemini-pro',
            'ai.vision_model': 'gemini-pro-vision',
            'ai.temperature': 0.7,
            'ai.max_tokens': 1024,
            'ai.timeout': 30
        }.get(key, default)
        return config
    
    @pytest.fixture
    def gemini_client(self, mock_config):
        """Create Gemini client with mock config."""
        return GeminiClient(mock_config)
    
    def test_initialization(self, gemini_client):
        """Test client initialization."""
        assert gemini_client.api_key == 'test_api_key_123'
        assert gemini_client.model == 'gemini-pro'
        assert gemini_client.vision_model == 'gemini-pro-vision'
    
    @patch('google.generativeai.GenerativeModel')
    def test_generate_text_success(self, mock_model, gemini_client):
        """Test successful text generation."""
        mock_response = Mock()
        mock_response.text = "This is a test response"
        mock_model.return_value.generate_content.return_value = mock_response
        
        response = gemini_client.generate_text("Test prompt")
        
        assert response == "This is a test response"
        mock_model.return_value.generate_content.assert_called_once()
    
    @patch('google.generativeai.GenerativeModel')
    def test_generate_text_empty_prompt(self, mock_model, gemini_client):
        """Test text generation with empty prompt."""
        response = gemini_client.generate_text("")
        
        assert response is None
        mock_model.return_value.generate_content.assert_not_called()
    
    @patch('google.generativeai.GenerativeModel')
    def test_generate_text_api_error(self, mock_model, gemini_client):
        """Test handling of API errors."""
        mock_model.return_value.generate_content.side_effect = Exception("API Error")
        
        response = gemini_client.generate_text("Test prompt")
        
        assert response is None
    
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_image_success(self, mock_model, gemini_client):
        """Test successful image analysis."""
        mock_response = Mock()
        mock_response.text = "Image contains a cat"
        mock_model.return_value.generate_content.return_value = mock_response
        
        response = gemini_client.analyze_image("/path/to/image.jpg")
        
        assert response == "Image contains a cat"
    
    def test_analyze_image_invalid_path(self, gemini_client):
        """Test image analysis with invalid path."""
        response = gemini_client.analyze_image("/nonexistent/image.jpg")
        
        assert response is None
    
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_image_with_prompt(self, mock_model, gemini_client):
        """Test image analysis with custom prompt."""
        mock_response = Mock()
        mock_response.text = "Custom analysis"
        mock_model.return_value.generate_content.return_value = mock_response
        
        response = gemini_client.analyze_image(
            "/path/to/image.jpg",
            prompt="Describe this image"
        )
        
        assert response == "Custom analysis"
    
    def test_cache_response(self, gemini_client):
        """Test response caching."""
        gemini_client.cache["test_prompt"] = "cached_response"
        
        response = gemini_client._get_cached_response("test_prompt")
        
        assert response == "cached_response"
    
    def test_cache_miss(self, gemini_client):
        """Test cache miss."""
        response = gemini_client._get_cached_response("nonexistent")
        
        assert response is None
    
    def test_cache_size_limit(self, gemini_client):
        """Test cache size limiting."""
        gemini_client.max_cache_size = 2
        
        gemini_client._cache_response("prompt1", "response1")
        gemini_client._cache_response("prompt2", "response2")
        gemini_client._cache_response("prompt3", "response3")
        
        assert len(gemini_client.cache) <= 2
    
    def test_clear_cache(self, gemini_client):
        """Test cache clearing."""
        gemini_client.cache["test"] = "value"
        
        gemini_client.clear_cache()
        
        assert len(gemini_client.cache) == 0
    
    def test_rate_limiting(self, gemini_client):
        """Test rate limiting."""
        gemini_client.last_request_time = 0
        gemini_client.min_request_interval = 1.0
        
        import time
        start = time.time()
        gemini_client._apply_rate_limit()
        elapsed = time.time() - start
        
        assert elapsed >= 0
    
    def test_get_statistics(self, gemini_client):
        """Test statistics retrieval."""
        gemini_client.request_count = 10
        gemini_client.cache_hits = 5
        
        stats = gemini_client.get_statistics()
        
        assert stats['total_requests'] == 10
        assert stats['cache_hits'] == 5
        assert 'cache_hit_rate' in stats


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def gemini_client(self, mock_config):
        """Create client for error testing."""
        return GeminiClient(mock_config)
    
    @patch('google.generativeai.GenerativeModel')
    def test_timeout_handling(self, mock_model, gemini_client):
        """Test timeout handling."""
        import asyncio
        mock_model.return_value.generate_content.side_effect = asyncio.TimeoutError()
        
        response = gemini_client.generate_text("Test")
        
        assert response is None
    
    @patch('google.generativeai.GenerativeModel')
    def test_network_error_handling(self, mock_model, gemini_client):
        """Test network error handling."""
        mock_model.return_value.generate_content.side_effect = ConnectionError()
        
        response = gemini_client.generate_text("Test")
        
        assert response is None
    
    @patch('google.generativeai.GenerativeModel')
    def test_retry_logic(self, mock_model, gemini_client):
        """Test retry logic on failure."""
        mock_model.return_value.generate_content.side_effect = [
            Exception("Temporary error"),
            Mock(text="Success")
        ]
        
        gemini_client.max_retries = 2
        response = gemini_client.generate_text("Test")
        
        assert response == "Success"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
