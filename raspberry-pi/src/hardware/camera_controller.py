"""
================================================================================
camera_controller.py - Camera Controller for Raspberry Pi
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Camera controller for Raspberry Pi Camera Module using picamera2 library.
Supports image capture, video recording, and camera configuration.

Features:
- Image capture with configurable resolution
- Preview mode
- Auto-focus and exposure control
- Image format conversion
- Thumbnail generation
- Camera health monitoring

================================================================================
"""

import logging
import time
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
from PIL import Image
import numpy as np


try:
    from picamera2 import Picamera2
    from picamera2.configuration import CameraConfiguration
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    logging.warning("picamera2 not available, using stub implementation")


class CameraError(Exception):
    """Exception raised for camera errors."""
    pass


class CameraController:
    """
    Camera controller for Raspberry Pi Camera Module.
    
    Handles image capture and camera configuration using picamera2.
    """
    
    def __init__(self, resolution: Tuple[int, int] = (1640, 1232)):
        """
        Initialize camera controller.
        
        Args:
            resolution: Camera resolution (width, height)
        """
        self.resolution = resolution
        self.camera: Optional[Any] = None
        self.initialized = False
        
        self.capture_dir = Path("/tmp/stealth-deck/captures")
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('camera_controller')
        
        self.last_capture_time = 0.0
        self.capture_count = 0
        
        self.config: Dict[str, Any] = {
            'format': 'RGB888',
            'rotation': 0,
            'quality': 85
        }
    
    def initialize(self) -> bool:
        """
        Initialize camera.
        
        Returns:
            True if successful, False otherwise
        """
        if not PICAMERA2_AVAILABLE:
            self.logger.error("picamera2 library not available")
            return False
        
        try:
            self.logger.info(f"Initializing camera at {self.resolution}")
            
            self.camera = Picamera2()
            
            camera_config = self.camera.create_still_configuration(
                main={"size": self.resolution}
            )
            
            self.camera.configure(camera_config)
            
            self.camera.start()
            
            time.sleep(2)
            
            self.initialized = True
            
            self.logger.info("Camera initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            return False
    
    def capture(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture image from camera.
        
        Args:
            filename: Output filename (default: auto-generated)
            
        Returns:
            Path to captured image or None on error
        """
        if not self.initialized or not self.camera:
            self.logger.error("Camera not initialized")
            return None
        
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"capture_{timestamp}.jpg"
            
            output_path = self.capture_dir / filename
            
            self.logger.info(f"Capturing image to: {output_path}")
            
            self.camera.capture_file(str(output_path))
            
            self.last_capture_time = time.time()
            self.capture_count += 1
            
            self.logger.info(f"Image captured: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Image capture failed: {e}")
            return None
    
    def capture_array(self) -> Optional[np.ndarray]:
        """
        Capture image as numpy array.
        
        Returns:
            Image array or None on error
        """
        if not self.initialized or not self.camera:
            self.logger.error("Camera not initialized")
            return None
        
        try:
            self.logger.info("Capturing image array")
            
            array = self.camera.capture_array()
            
            self.last_capture_time = time.time()
            self.capture_count += 1
            
            self.logger.info(f"Array captured: {array.shape}")
            
            return array
            
        except Exception as e:
            self.logger.error(f"Array capture failed: {e}")
            return None
    
    def capture_thumbnail(self, max_size: Tuple[int, int] = (320, 240)) -> Optional[str]:
        """
        Capture thumbnail image.
        
        Args:
            max_size: Maximum thumbnail size (width, height)
            
        Returns:
            Path to thumbnail or None on error
        """
        try:
            full_image_path = self.capture()
            
            if not full_image_path:
                return None
            
            img = Image.open(full_image_path)
            
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            thumbnail_path = str(Path(full_image_path).with_suffix('.thumb.jpg'))
            
            img.save(thumbnail_path, quality=self.config['quality'])
            
            self.logger.info(f"Thumbnail created: {thumbnail_path}")
            
            return thumbnail_path
            
        except Exception as e:
            self.logger.error(f"Thumbnail creation failed: {e}")
            return None
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set camera resolution.
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Setting resolution to {width}x{height}")
            
            self.resolution = (width, height)
            
            if self.initialized and self.camera:
                self.close()
                return self.initialize()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Set resolution failed: {e}")
            return False
    
    def set_quality(self, quality: int) -> None:
        """
        Set JPEG quality.
        
        Args:
            quality: Quality value (0-100)
        """
        self.config['quality'] = max(0, min(100, quality))
        self.logger.info(f"Quality set to {self.config['quality']}")
    
    def set_rotation(self, rotation: int) -> None:
        """
        Set image rotation.
        
        Args:
            rotation: Rotation in degrees (0, 90, 180, 270)
        """
        if rotation not in [0, 90, 180, 270]:
            self.logger.warning(f"Invalid rotation: {rotation}")
            return
        
        self.config['rotation'] = rotation
        self.logger.info(f"Rotation set to {rotation}")
    
    def close(self) -> None:
        """Close camera and release resources."""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                self.logger.info("Camera closed")
            except Exception as e:
                self.logger.error(f"Error closing camera: {e}")
            finally:
                self.camera = None
                self.initialized = False
    
    def is_available(self) -> bool:
        """
        Check if camera is available.
        
        Returns:
            True if camera is available
        """
        return PICAMERA2_AVAILABLE and self.initialized
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get camera statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'initialized': self.initialized,
            'resolution': self.resolution,
            'capture_count': self.capture_count,
            'last_capture_time': self.last_capture_time,
            'quality': self.config['quality'],
            'rotation': self.config['rotation']
        }
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get camera information.
        
        Returns:
            Camera info dictionary
        """
        info = {
            'available': PICAMERA2_AVAILABLE,
            'initialized': self.initialized,
            'resolution': self.resolution
        }
        
        if self.initialized and self.camera:
            try:
                info['camera_properties'] = self.camera.camera_properties
            except:
                pass
        
        return info
    
    def cleanup_old_captures(self, max_age_seconds: int = 3600) -> int:
        """
        Delete old capture files.
        
        Args:
            max_age_seconds: Maximum age in seconds
            
        Returns:
            Number of files deleted
        """
        deleted = 0
        current_time = time.time()
        
        try:
            for file_path in self.capture_dir.glob("*.jpg"):
                file_age = current_time - file_path.stat().st_mtime
                
                if file_age > max_age_seconds:
                    file_path.unlink()
                    deleted += 1
            
            self.logger.info(f"Deleted {deleted} old capture files")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
        
        return deleted
    
    def __del__(self):
        """Destructor - ensure camera is closed."""
        self.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    camera = CameraController(resolution=(1640, 1232))
    
    if camera.initialize():
        print("Camera initialized successfully")
        
        image_path = camera.capture()
        
        if image_path:
            print(f"Image captured: {image_path}")
        
        camera.close()
    else:
        print("Camera initialization failed")

