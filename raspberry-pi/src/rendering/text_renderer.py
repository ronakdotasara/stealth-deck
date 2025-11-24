"""
================================================================================
text_renderer.py - Text to Bitmap Renderer
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Renders text to bitmap images suitable for ESP32 OLED display.
Handles font loading, text wrapping, and image generation.

Features:
- Multiple font support
- Text wrapping for narrow display
- Anti-aliasing
- Monochrome and grayscale output
- Line spacing control
- Alignment options

================================================================================
"""

import logging
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


class TextRenderer:
    """
    Text to bitmap renderer for display output.
    
    Renders text with proper wrapping and formatting for OLED display.
    """
    
    def __init__(self, display_width: int = 240, display_height: int = 536):
        """
        Initialize text renderer.
        
        Args:
            display_width: Display width in pixels
            display_height: Display height in pixels
        """
        self.display_width = display_width
        self.display_height = display_height
        
        self.logger = logging.getLogger('text_renderer')
        
        self.font_dir = Path(__file__).parent.parent.parent / 'data' / 'fonts'
        
        self.default_font_size = 12
        self.line_spacing = 1.2
        self.margin = 5
        
        self.fonts = {}
        self._load_fonts()
        
        self.char_width = 6
        self.max_chars_per_line = (display_width - 2 * self.margin) // self.char_width
    
    def _load_fonts(self) -> None:
        """Load available fonts."""
        try:
            default_font = self.font_dir / 'Roboto-Regular.ttf'
            mono_font = self.font_dir / 'RobotoMono-Regular.ttf'
            
            if default_font.exists():
                self.fonts['default'] = ImageFont.truetype(str(default_font), self.default_font_size)
                self.fonts['default_bold'] = ImageFont.truetype(str(default_font), self.default_font_size + 2)
            else:
                self.fonts['default'] = ImageFont.load_default()
                self.fonts['default_bold'] = ImageFont.load_default()
            
            if mono_font.exists():
                self.fonts['mono'] = ImageFont.truetype(str(mono_font), self.default_font_size - 1)
            else:
                self.fonts['mono'] = self.fonts['default']
            
            self.logger.info("Fonts loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Font loading failed: {e}")
            self.fonts['default'] = ImageFont.load_default()
            self.fonts['default_bold'] = ImageFont.load_default()
            self.fonts['mono'] = ImageFont.load_default()
    
    def render_text(self, text: str, font_name: str = 'default',
                   mode: str = '1') -> Optional[Image.Image]:
        """
        Render text to image.
        
        Args:
            text: Text to render
            font_name: Font to use ('default', 'default_bold', 'mono')
            mode: PIL image mode ('1' for monochrome, 'L' for grayscale)
            
        Returns:
            PIL Image or None
        """
        try:
            if not text:
                return None
            
            lines = self._wrap_text(text)
            
            font = self.fonts.get(font_name, self.fonts['default'])
            
            line_height = int(self.default_font_size * self.line_spacing)
            
            content_height = len(lines) * line_height + 2 * self.margin
            height = min(content_height, self.display_height)
            
            if mode == '1':
                img = Image.new('1', (self.display_width, height), color=0)
            else:
                img = Image.new('L', (self.display_width, height), color=0)
            
            draw = ImageDraw.Draw(img)
            
            y = self.margin
            for line in lines:
                if y + line_height > height:
                    break
                
                draw.text((self.margin, y), line, font=font, fill=255 if mode == 'L' else 1)
                y += line_height
            
            return img
            
        except Exception as e:
            self.logger.error(f"Text rendering failed: {e}")
            return None
    
    def render_multiline(self, lines: list, font_name: str = 'default',
                        mode: str = '1') -> Optional[Image.Image]:
        """
        Render pre-formatted lines.
        
        Args:
            lines: List of text lines
            font_name: Font to use
            mode: Image mode
            
        Returns:
            PIL Image or None
        """
        try:
            font = self.fonts.get(font_name, self.fonts['default'])
            
            line_height = int(self.default_font_size * self.line_spacing)
            
            content_height = len(lines) * line_height + 2 * self.margin
            height = min(content_height, self.display_height)
            
            if mode == '1':
                img = Image.new('1', (self.display_width, height), color=0)
            else:
                img = Image.new('L', (self.display_width, height), color=0)
            
            draw = ImageDraw.Draw(img)
            
            y = self.margin
            for line in lines:
                if y + line_height > height:
                    break
                
                draw.text((self.margin, y), line, font=font, fill=255 if mode == 'L' else 1)
                y += line_height
            
            return img
            
        except Exception as e:
            self.logger.error(f"Multiline rendering failed: {e}")
            return None
    
    def render_centered(self, text: str, font_name: str = 'default',
                       mode: str = '1') -> Optional[Image.Image]:
        """
        Render text centered.
        
        Args:
            text: Text to render
            font_name: Font to use
            mode: Image mode
            
        Returns:
            PIL Image or None
        """
        try:
            font = self.fonts.get(font_name, self.fonts['default'])
            
            if mode == '1':
                img = Image.new('1', (self.display_width, self.display_height), color=0)
            else:
                img = Image.new('L', (self.display_width, self.display_height), color=0)
            
            draw = ImageDraw.Draw(img)
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.display_width - text_width) // 2
            y = (self.display_height - text_height) // 2
            
            draw.text((x, y), text, font=font, fill=255 if mode == 'L' else 1)
            
            return img
            
        except Exception as e:
            self.logger.error(f"Centered rendering failed: {e}")
            return None
    
    def _wrap_text(self, text: str, max_width: Optional[int] = None) -> list:
        """
        Wrap text to fit display width.
        
        Args:
            text: Text to wrap
            max_width: Maximum characters per line
            
        Returns:
            List of wrapped lines
        """
        if max_width is None:
            max_width = self.max_chars_per_line
        
        lines = []
        
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append('')
                continue
            
            words = paragraph.split()
            current_line = []
            current_length = 0
            
            for word in words:
                word_length = len(word)
                
                if current_length + word_length + len(current_line) <= max_width:
                    current_line.append(word)
                    current_length += word_length
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
            
            if current_line:
                lines.append(' '.join(current_line))
        
        return lines
    
    def image_to_bytes(self, img: Image.Image) -> bytes:
        """
        Convert PIL image to bytes.
        
        Args:
            img: PIL Image
            
        Returns:
            Image data as bytes
        """
        import io
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        
        return buffer.getvalue()
    
    def render_to_bytes(self, text: str, font_name: str = 'default',
                       mode: str = '1') -> Optional[bytes]:
        """
        Render text directly to bytes.
        
        Args:
            text: Text to render
            font_name: Font to use
            mode: Image mode
            
        Returns:
            Image bytes or None
        """
        img = self.render_text(text, font_name, mode)
        
        if img:
            return self.image_to_bytes(img)
        
        return None
    
    def get_text_dimensions(self, text: str, font_name: str = 'default') -> Tuple[int, int]:
        """
        Get dimensions of rendered text.
        
        Args:
            text: Text to measure
            font_name: Font to use
            
        Returns:
            Tuple of (width, height)
        """
        try:
            font = self.fonts.get(font_name, self.fonts['default'])
            
            img = Image.new('1', (1, 1))
            draw = ImageDraw.Draw(img)
            
            bbox = draw.textbbox((0, 0), text, font=font)
            
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            
            return (width, height)
            
        except Exception as e:
            self.logger.error(f"Dimension calculation failed: {e}")
            return (0, 0)
    
    def set_font_size(self, size: int) -> None:
        """
        Set default font size.
        
        Args:
            size: Font size in points
        """
        self.default_font_size = size
        self._load_fonts()
    
    def set_line_spacing(self, spacing: float) -> None:
        """
        Set line spacing multiplier.
        
        Args:
            spacing: Line spacing (1.0 = single, 1.5 = 1.5x, etc.)
        """
        self.line_spacing = spacing


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    renderer = TextRenderer()
    
    text = "This is a test of the text rendering system. It should wrap properly."
    
    img = renderer.render_text(text)
    
    if img:
        img.save('/tmp/test_render.png')
        print(f"Rendered image: {img.size}")
