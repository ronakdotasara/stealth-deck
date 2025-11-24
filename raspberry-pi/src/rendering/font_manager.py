"""
================================================================================
font_manager.py - Font Management System
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Manages font loading and caching for text rendering.
Supports TTF fonts with multiple sizes and styles.

Features:
- Font caching
- Multiple font sizes
- Font fallback
- Emoji font support
- Memory-efficient loading

================================================================================
"""

import logging
from typing import Optional, Dict
from pathlib import Path
from PIL import ImageFont


class FontManager:
    """
    Font management system.
    
    Handles loading, caching, and retrieval of fonts.
    """
    
    def __init__(self, font_dir: Optional[str] = None):
        """
        Initialize font manager.
        
        Args:
            font_dir: Directory containing font files
        """
        self.logger = logging.getLogger('font_manager')
        
        if font_dir:
            self.font_dir = Path(font_dir)
        else:
            self.font_dir = Path(__file__).parent.parent.parent / 'data' / 'fonts'
        
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
        
        self.default_fonts = {
            'regular': 'Roboto-Regular.ttf',
            'bold': 'Roboto-Bold.ttf',
            'mono': 'RobotoMono-Regular.ttf',
            'emoji': 'NotoEmoji-Regular.ttf'
        }
        
        self.default_size = 12
        
        self._ensure_font_dir()
    
    def _ensure_font_dir(self) -> None:
        """Ensure font directory exists."""
        if not self.font_dir.exists():
            self.logger.warning(f"Font directory not found: {self.font_dir}")
            self.font_dir.mkdir(parents=True, exist_ok=True)
    
    def get_font(self, font_name: str = 'regular', size: int = 12) -> ImageFont.FreeTypeFont:
        """
        Get font by name and size.
        
        Args:
            font_name: Font name ('regular', 'bold', 'mono', 'emoji')
            size: Font size in points
            
        Returns:
            PIL ImageFont object
        """
        cache_key = f"{font_name}_{size}"
        
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        font = self._load_font(font_name, size)
        
        self.font_cache[cache_key] = font
        
        return font
    
    def _load_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Load font from disk.
        
        Args:
            font_name: Font name
            size: Font size
            
        Returns:
            Loaded font
        """
        try:
            font_filename = self.default_fonts.get(font_name)
            
            if not font_filename:
                self.logger.warning(f"Unknown font: {font_name}")
                return ImageFont.load_default()
            
            font_path = self.font_dir / font_filename
            
            if not font_path.exists():
                self.logger.warning(f"Font file not found: {font_path}")
                return ImageFont.load_default()
            
            font = ImageFont.truetype(str(font_path), size)
            
            self.logger.debug(f"Loaded font: {font_name} size {size}")
            
            return font
            
        except Exception as e:
            self.logger.error(f"Font loading failed: {e}")
            return ImageFont.load_default()
    
    def get_font_by_path(self, font_path: str, size: int = 12) -> ImageFont.FreeTypeFont:
        """
        Load font from custom path.
        
        Args:
            font_path: Path to font file
            size: Font size
            
        Returns:
            Loaded font
        """
        try:
            path = Path(font_path)
            
            if not path.exists():
                self.logger.warning(f"Font not found: {font_path}")
                return ImageFont.load_default()
            
            cache_key = f"{path.name}_{size}"
            
            if cache_key in self.font_cache:
                return self.font_cache[cache_key]
            
            font = ImageFont.truetype(str(path), size)
            
            self.font_cache[cache_key] = font
            
            return font
            
        except Exception as e:
            self.logger.error(f"Custom font loading failed: {e}")
            return ImageFont.load_default()
    
    def clear_cache(self) -> None:
        """Clear font cache."""
        self.font_cache.clear()
        self.logger.info("Font cache cleared")
    
    def list_available_fonts(self) -> list:
        """
        List all available fonts.
        
        Returns:
            List of font names
        """
        fonts = []
        
        if self.font_dir.exists():
            for font_file in self.font_dir.glob('*.ttf'):
                fonts.append(font_file.stem)
        
        return fonts
    
    def get_font_info(self, font_name: str) -> Dict[str, any]:
        """
        Get information about a font.
        
        Args:
            font_name: Font name
            
        Returns:
            Font information dictionary
        """
        font_filename = self.default_fonts.get(font_name)
        
        if not font_filename:
            return {'exists': False}
        
        font_path = self.font_dir / font_filename
        
        if not font_path.exists():
            return {'exists': False}
        
        return {
            'exists': True,
            'path': str(font_path),
            'size': font_path.stat().st_size,
            'cached': any(font_name in key for key in self.font_cache.keys())
        }
    
    def preload_fonts(self, sizes: list = None) -> None:
        """
        Preload commonly used fonts.
        
        Args:
            sizes: List of font sizes to preload
        """
        if sizes is None:
            sizes = [10, 12, 14, 16]
        
        for font_name in self.default_fonts.keys():
            for size in sizes:
                self.get_font(font_name, size)
        
        self.logger.info(f"Preloaded {len(self.font_cache)} fonts")
    
    def get_cache_size(self) -> int:
        """
        Get number of cached fonts.
        
        Returns:
            Cache size
        """
        return len(self.font_cache)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    manager = FontManager()
    
    font = manager.get_font('regular', 12)
    print(f"Loaded font: {font}")
    
    available = manager.list_available_fonts()
    print(f"Available fonts: {available}")
    
    info = manager.get_font_info('regular')
    print(f"Font info: {info}")
