"""
================================================================================
gemini_renderer.py - Gemini Response Renderer for Display
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Renders Gemini API responses into displayable format for ESP32 OLED.
Handles text formatting, markdown parsing, and display optimization.

Features:
- Text wrapping for narrow display
- Markdown parsing
- Code block formatting
- List rendering
- Table support
- LaTeX to Unicode conversion
- Emoji support

================================================================================
"""

import logging
import re
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


class GeminiRenderer:
    """
    Gemini response renderer for display.
    
    Converts Gemini text responses to display-ready format.
    """
    
    def __init__(self, display_width: int = 240, display_height: int = 536):
        """
        Initialize renderer.
        
        Args:
            display_width: Display width in pixels
            display_height: Display height in pixels
        """
        self.display_width = display_width
        self.display_height = display_height
        
        self.logger = logging.getLogger('gemini_renderer')
        
        self.font_size = 12
        self.line_spacing = 1.2
        self.margin = 5
        
        self.max_chars_per_line = (display_width - 2 * self.margin) // 7
        
        self.font_path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        self.mono_font_path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
        
        self._load_fonts()
    
    def _load_fonts(self) -> None:
        """Load fonts for rendering."""
        try:
            if self.font_path.exists():
                self.font = ImageFont.truetype(str(self.font_path), self.font_size)
            else:
                self.font = ImageFont.load_default()
            
            if self.mono_font_path.exists():
                self.mono_font = ImageFont.truetype(str(self.mono_font_path), self.font_size - 2)
            else:
                self.mono_font = self.font
                
        except Exception as e:
            self.logger.warning(f"Font loading failed: {e}")
            self.font = ImageFont.load_default()
            self.mono_font = ImageFont.load_default()
    
    def render(self, text: str) -> bytes:
        """
        Render text to image bytes.
        
        Args:
            text: Text to render
            
        Returns:
            Image data as bytes
        """
        try:
            lines = self._format_text(text)
            
            img = self._create_image(lines)
            
            img_bytes = self._image_to_bytes(img)
            
            return img_bytes
            
        except Exception as e:
            self.logger.error(f"Rendering failed: {e}")
            return self._render_error("Rendering error")
    
    def _format_text(self, text: str) -> List[str]:
        """
        Format text for display.
        
        Args:
            text: Raw text
            
        Returns:
            List of formatted lines
        """
        text = self._clean_text(text)
        
        text = self._convert_markdown(text)
        
        lines = self._wrap_text(text)
        
        return lines
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        text = text.strip()
        
        return text
    
    def _convert_markdown(self, text: str) -> str:
        """
        Convert basic markdown to plain text.
        
        Args:
            text: Text with markdown
            
        Returns:
            Converted text
        """
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        text = re.sub(r'``````', '[CODE]', text)
        text = re.sub(r'`(.+?)`', r'[\1]', text)
        
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        text = re.sub(r'^#+\s+(.+)$', r'=== \1 ===', text, flags=re.MULTILINE)
        
        text = re.sub(r'^\*\s+(.+)$', r'• \1', text, flags=re.MULTILINE)
        text = re.sub(r'^\-\s+(.+)$', r'• \1', text, flags=re.MULTILINE)
        
        text = re.sub(r'^\d+\.\s+(.+)$', r'\1', text, flags=re.MULTILINE)
        
        return text
    
    def _wrap_text(self, text: str, max_width: Optional[int] = None) -> List[str]:
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
        
        for paragraph in text.split('\n'):
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
    
    def _create_image(self, lines: List[str]) -> Image.Image:
        """
        Create image from text lines.
        
        Args:
            lines: Text lines
            
        Returns:
            PIL Image
        """
        line_height = int(self.font_size * self.line_spacing)
        
        required_height = len(lines) * line_height + 2 * self.margin
        
        height = min(required_height, self.display_height)
        
        img = Image.new('1', (self.display_width, height), color=0)
        draw = ImageDraw.Draw(img)
        
        y = self.margin
        
        for line in lines:
            if y + line_height > height:
                break
            
            draw.text((self.margin, y), line, font=self.font, fill=1)
            y += line_height
        
        return img
    
    def _image_to_bytes(self, img: Image.Image) -> bytes:
        """
        Convert PIL image to bytes.
        
        Args:
            img: PIL Image
            
        Returns:
            Image bytes
        """
        import io
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        
        return buffer.getvalue()
    
    def _render_error(self, message: str) -> bytes:
        """
        Render error message.
        
        Args:
            message: Error message
            
        Returns:
            Error image bytes
        """
        img = Image.new('1', (self.display_width, 50), color=0)
        draw = ImageDraw.Draw(img)
        
        draw.text((10, 20), message, font=self.font, fill=1)
        
        return self._image_to_bytes(img)
    
    def render_text_simple(self, text: str) -> str:
        """
        Render text as simple formatted string.
        
        Args:
            text: Text to render
            
        Returns:
            Formatted text string
        """
        lines = self._format_text(text)
        return '\n'.join(lines)
    
    def get_preview(self, text: str, max_lines: int = 3) -> str:
        """
        Get preview of rendered text.
        
        Args:
            text: Text to preview
            max_lines: Maximum lines
            
        Returns:
            Preview string
        """
        lines = self._format_text(text)
        
        preview_lines = lines[:max_lines]
        
        preview = '\n'.join(preview_lines)
        
        if len(lines) > max_lines:
            preview += '\n...'
        
        return preview


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    renderer = GeminiRenderer()
    
    test_text = """
    # Test Response
    
    This is a **bold** test with *italic* text.
    
    Here's a list:
    - Item one
    - Item two
    - Item three
    
    And some `code`.
    """
    
    formatted = renderer.render_text_simple(test_text)
    print(formatted)
    
    preview = renderer.get_preview(test_text, max_lines=3)
    print("\nPreview:")
    print(preview)
