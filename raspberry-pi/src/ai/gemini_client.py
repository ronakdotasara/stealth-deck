"""
================================================================================
gemini_client.py - Google Gemini API Client for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Client for interacting with Google's Gemini API for AI-powered features.
Supports text generation, image analysis, and conversation management.

Features:
- Text generation with Gemini Pro
- Image analysis with Gemini Pro Vision
- Conversation history management
- Rate limiting and retry logic
- Response caching
- Error handling
- Async support

================================================================================
"""

import google.generativeai as genai
import logging
import time
import hashlib
from typing import Optional, List, Dict, Any
from pathlib import Path
from PIL import Image


class GeminiError(Exception):
    """Exception raised for Gemini API errors."""
    pass


class GeminiClient:
    """
    Client for Google Gemini API.
    
    Handles text generation, image analysis, and conversation management.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key
            model_name: Model name (default: gemini-pro)
        """
        self.api_key = api_key
        self.model_name = model_name
        
        self.logger = logging.getLogger('gemini_client')
        
        self.conversation_history: List[Dict[str, str]] = []
        self.cache: Dict[str, str] = {}
        
        self.rate_limit_delay = 1.0
        self.last_request_time = 0.0
        
        self.max_retries = 3
        self.retry_delay = 2.0
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Gemini API client."""
        try:
            genai.configure(api_key=self.api_key)
            
            self.model = genai.GenerativeModel(self.model_name)
            self.vision_model = genai.GenerativeModel('gemini-pro-vision')
            
            self.chat = self.model.start_chat(history=[])
            
            self.logger.info(f"Gemini client initialized with model: {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            raise GeminiError(f"Initialization failed: {e}")
    
    def generate_text(self, prompt: str, use_cache: bool = True) -> Optional[str]:
        """
        Generate text response from prompt.
        
        Args:
            prompt: Input prompt
            use_cache: Use cached response if available
            
        Returns:
            Generated text or None on error
        """
        if use_cache:
            cache_key = self._get_cache_key(prompt)
            if cache_key in self.cache:
                self.logger.debug("Returning cached response")
                return self.cache[cache_key]
        
        self._rate_limit()
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Generating text (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.model.generate_content(prompt)
                
                if not response or not response.text:
                    self.logger.warning("Empty response from Gemini")
                    return None
                
                text = response.text
                
                if use_cache:
                    self.cache[cache_key] = text
                
                self.logger.info(f"Generated {len(text)} characters")
                
                return text
                
            except Exception as e:
                self.logger.error(f"Generate text error (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise GeminiError(f"Text generation failed: {e}")
        
        return None
    
    def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> Optional[str]:
        """
        Analyze image with Gemini Vision.
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            
        Returns:
            Analysis text or None on error
        """
        try:
            self.logger.info(f"Analyzing image: {image_path}")
            
            if not Path(image_path).exists():
                raise GeminiError(f"Image file not found: {image_path}")
            
            img = Image.open(image_path)
            
            self._rate_limit()
            
            response = self.vision_model.generate_content([prompt, img])
            
            if not response or not response.text:
                self.logger.warning("Empty response from Gemini Vision")
                return None
            
            text = response.text
            
            self.logger.info(f"Analysis complete: {len(text)} characters")
            
            return text
            
        except Exception as e:
            self.logger.error(f"Image analysis error: {e}")
            raise GeminiError(f"Image analysis failed: {e}")
    
    def chat_message(self, message: str) -> Optional[str]:
        """
        Send message in conversation context.
        
        Args:
            message: User message
            
        Returns:
            Response text or None on error
        """
        try:
            self.logger.info("Sending chat message")
            
            self._rate_limit()
            
            response = self.chat.send_message(message)
            
            if not response or not response.text:
                self.logger.warning("Empty response from chat")
                return None
            
            text = response.text
            
            self.conversation_history.append({
                'role': 'user',
                'content': message
            })
            self.conversation_history.append({
                'role': 'model',
                'content': text
            })
            
            self.logger.info(f"Chat response: {len(text)} characters")
            
            return text
            
        except Exception as e:
            self.logger.error(f"Chat message error: {e}")
            raise GeminiError(f"Chat message failed: {e}")
    
    def clear_conversation(self) -> None:
        """Clear conversation history and start new chat."""
        self.conversation_history = []
        self.chat = self.model.start_chat(history=[])
        self.logger.info("Conversation cleared")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.conversation_history.copy()
    
    def clear_cache(self) -> None:
        """Clear response cache."""
        self.cache.clear()
        self.logger.info("Cache cleared")
    
    def _rate_limit(self) -> None:
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key from text.
        
        Args:
            text: Input text
            
        Returns:
            Cache key (hash)
        """
        return hashlib.md5(text.encode()).hexdigest()
    
    def set_rate_limit(self, delay: float) -> None:
        """
        Set rate limit delay.
        
        Args:
            delay: Delay in seconds between requests
        """
        self.rate_limit_delay = delay
        self.logger.info(f"Rate limit set to {delay}s")
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get model information.
        
        Returns:
            Model info dictionary
        """
        return {
            'name': self.model_name,
            'vision_model': 'gemini-pro-vision',
            'cache_size': len(self.cache),
            'conversation_length': len(self.conversation_history)
        }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python gemini_client.py <api_key>")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    
    client = GeminiClient(sys.argv[1])
    
    response = client.generate_text("Tell me a short joke about computers.")
    print(f"Response: {response}")

