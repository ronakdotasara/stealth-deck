"""
================================================================================
image_preprocessor.py - Image Preprocessing for AI
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Preprocesses images before sending to Gemini API.
Optimizes size, format, and quality for efficient API usage.

Features:
- Image resizing
- Format conversion
- Quality optimization
- EXIF stripping
- Compression

================================================================================
"""

import logging
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image
import io


class ImagePreprocessor:
    """
    Image preprocessing for AI analysis.
    
    Optimizes images for Gemini API.
    """
    
    def __init__(self, max_size: int = 1024, quality: int = 85):
        """
        Initialize image preprocessor.
        
        Args:
            max_size: Maximum dimension (width or height)
            quality: JPEG quality (1-100)
        """
        self.logger = logging.getLogger('image_preprocessor')
        
        self.max_size = max_size
        self.quality = quality
        
        self.supported_formats = ['JPEG', 'PNG', 'WEBP']
    
    def preprocess(self, image_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Preprocess image file.
        
        Args:
            image_path: Input image path
            output_path: Output path (optional)
            
        Returns:
            Output path or None
        """
        try:
            image_path = Path(image_path)
            
            if not image_path.exists():
                self.logger.error(f"Image not found: {image_path}")
                return None
            
            img = Image.open(image_path)
            
            processed = self.process_image(img)
            
            if output_path is None:
                output_path = str(image_path.with_suffix('.processed.jpg'))
            
            processed.save(output_path, 'JPEG', quality=self.quality, optimize=True)
            
            original_size = image_path.stat().st_size
            processed_size = Path(output_path).stat().st_size
            
            self.logger.info(f"Processed: {original_size} -> {processed_size} bytes "
                           f"({(1 - processed_size/original_size)*100:.1f}% reduction)")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Preprocessing failed: {e}")
            return None
    
    def process_image(self, img: Image.Image) -> Image.Image:
        """
        Process PIL Image.
        
        Args:
            img: Input image
            
        Returns:
            Processed image
        """
        img = self.resize_image(img)
        
        img = self.convert_mode(img)
        
        img = self.strip_exif(img)
        
        return img
    
    def resize_image(self, img: Image.Image) -> Image.Image:
        """
        Resize image to max dimensions.
        
        Args:
            img: Input image
            
        Returns:
            Resized image
        """
        width, height = img.size
        
        if width <= self.max_size and height <= self.max_size:
            return img
        
        if width > height:
            new_width = self.max_size
            new_height = int(height * (self.max_size / width))
        else:
            new_height = self.max_size
            new_width = int(width * (self.max_size / height))
        
        resized = img.resize((new_width, new_height), Image.LANCZOS)
        
        self.logger.debug(f"Resized: {width}x{height} -> {new_width}x{new_height}")
        
        return resized
    
    def convert_mode(self, img: Image.Image) -> Image.Image:
        """
        Convert image to RGB mode.
        
        Args:
            img: Input image
            
        Returns:
            Converted image
        """
        if img.mode == 'RGB':
            return img
        
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            return background
        
        return img.convert('RGB')
    
    def strip_exif(self, img: Image.Image) -> Image.Image:
        """
        Strip EXIF data from image.
        
        Args:
            img: Input image
            
        Returns:
            Image without EXIF
        """
        data = list(img.getdata())
        image_without_exif = Image.new(img.mode, img.size)
        image_without_exif.putdata(data)
        
        return image_without_exif
    
    def compress_to_target_size(self, img: Image.Image, 
                                target_kb: int = 500) -> bytes:
        """
        Compress image to target file size.
        
        Args:
            img: Input image
            target_kb: Target size in KB
            
        Returns:
            Compressed image bytes
        """
        target_bytes = target_kb * 1024
        
        quality = self.quality
        
        while quality > 10:
            buffer = io.BytesIO()
            img.save(buffer, 'JPEG', quality=quality, optimize=True)
            size = buffer.tell()
            
            if size <= target_bytes:
                return buffer.getvalue()
            
            quality -= 5
        
        buffer = io.BytesIO()
        img.save(buffer, 'JPEG', quality=10, optimize=True)
        return buffer.getvalue()
    
    def enhance_contrast(self, img: Image.Image, factor: float = 1.2) -> Image.Image:
        """
        Enhance image contrast.
        
        Args:
            img: Input image
            factor: Contrast factor (1.0 = no change)
            
        Returns:
            Enhanced image
        """
        from PIL import ImageEnhance
        
        enhancer = ImageEnhance.Contrast(img)
        enhanced = enhancer.enhance(factor)
        
        return enhanced
    
    def enhance_sharpness(self, img: Image.Image, factor: float = 1.5) -> Image.Image:
        """
        Enhance image sharpness.
        
        Args:
            img: Input image
            factor: Sharpness factor (1.0 = no change)
            
        Returns:
            Enhanced image
        """
        from PIL import ImageEnhance
        
        enhancer = ImageEnhance.Sharpness(img)
        enhanced = enhancer.enhance(factor)
        
        return enhanced
    
    def adjust_brightness(self, img: Image.Image, factor: float = 1.0) -> Image.Image:
        """
        Adjust image brightness.
        
        Args:
            img: Input image
            factor: Brightness factor (1.0 = no change)
            
        Returns:
            Adjusted image
        """
        from PIL import ImageEnhance
        
        enhancer = ImageEnhance.Brightness(img)
        adjusted = enhancer.enhance(factor)
        
        return adjusted
    
    def auto_enhance(self, img: Image.Image) -> Image.Image:
        """
        Auto-enhance image for OCR/analysis.
        
        Args:
            img: Input image
            
        Returns:
            Enhanced image
        """
        img = self.enhance_contrast(img, 1.2)
        
        img = self.enhance_sharpness(img, 1.3)
        
        return img
    
    def get_image_info(self, image_path: str) -> dict:
        """
        Get image information.
        
        Args:
            image_path: Image path
            
        Returns:
            Image info dictionary
        """
        try:
            img = Image.open(image_path)
            
            return {
                'size': img.size,
                'mode': img.mode,
                'format': img.format,
                'file_size': Path(image_path).stat().st_size,
                'megapixels': (img.size[0] * img.size[1]) / 1000000
            }
            
        except Exception as e:
            self.logger.error(f"Get image info failed: {e}")
            return {}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    preprocessor = ImagePreprocessor()
    
    print("Image preprocessor initialized")
