"""
================================================================================
markdown_parser.py - Markdown Parser for Display Rendering
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Parses markdown text and converts to display-friendly format.
Handles headings, lists, code blocks, emphasis, and links.

Features:
- Basic markdown syntax support
- Display-optimized output
- Emoji support
- Code block detection
- List formatting
- Link extraction

================================================================================
"""

import logging
import re
from typing import List, Dict, Any


class MarkdownParser:
    """
    Markdown parser for text formatting.
    
    Converts markdown to plain text suitable for small displays.
    """
    
    def __init__(self):
        """Initialize markdown parser."""
        self.logger = logging.getLogger('markdown_parser')
        
        self.patterns = {
            'heading': re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),
            'bold': re.compile(r'\*\*(.+?)\*\*'),
            'italic': re.compile(r'\*(.+?)\*'),
            'underline': re.compile(r'__(.+?)__'),
            'strikethrough': re.compile(r'~~(.+?)~~'),
            'code_inline': re.compile(r'`(.+?)`'),
            'code_block': re.compile(r'``````', re.DOTALL),
            'link': re.compile(r'\[(.+?)\]\((.+?)\)'),
            'image': re.compile(r'!\[(.+?)\]\((.+?)\)'),
            'unordered_list': re.compile(r'^[\*\-\+]\s+(.+)$', re.MULTILINE),
            'ordered_list': re.compile(r'^\d+\.\s+(.+)$', re.MULTILINE),
            'blockquote': re.compile(r'^>\s+(.+)$', re.MULTILINE),
            'horizontal_rule': re.compile(r'^[\*\-_]{3,}$', re.MULTILINE),
        }
    
    def parse(self, text: str) -> str:
        """
        Parse markdown text.
        
        Args:
            text: Markdown text
            
        Returns:
            Formatted plain text
        """
        try:
            result = text
            
            result = self._parse_code_blocks(result)
            
            result = self._parse_headings(result)
            
            result = self._parse_lists(result)
            
            result = self._parse_blockquotes(result)
            
            result = self._parse_emphasis(result)
            
            result = self._parse_links(result)
            
            result = self._parse_inline_code(result)
            
            result = self._cleanup(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Markdown parsing failed: {e}")
            return text
    
    def _parse_code_blocks(self, text: str) -> str:
        """Parse code blocks."""
        def replace_code_block(match):
            language = match.group(1)
            code = match.group(2)
            
            lines = code.strip().split('\n')
            formatted = '\n'.join(f"  {line}" for line in lines)
            
            return f"\n[CODE]\n{formatted}\n[/CODE]\n"
        
        return self.patterns['code_block'].sub(replace_code_block, text)
    
    def _parse_headings(self, text: str) -> str:
        """Parse headings."""
        def replace_heading(match):
            level = len(match.group(1))
            title = match.group(2)
            
            if level == 1:
                return f"\n{'=' * len(title)}\n{title}\n{'=' * len(title)}\n"
            elif level == 2:
                return f"\n{title}\n{'-' * len(title)}\n"
            else:
                return f"\n{title}\n"
        
        return self.patterns['heading'].sub(replace_heading, text)
    
    def _parse_lists(self, text: str) -> str:
        """Parse lists."""
        text = self.patterns['unordered_list'].sub(r'• \1', text)
        
        text = self.patterns['ordered_list'].sub(r'\1', text)
        
        return text
    
    def _parse_blockquotes(self, text: str) -> str:
        """Parse blockquotes."""
        return self.patterns['blockquote'].sub(r'| \1', text)
    
    def _parse_emphasis(self, text: str) -> str:
        """Parse emphasis (bold, italic, etc.)."""
        text = self.patterns['bold'].sub(r'\1', text)
        
        text = self.patterns['italic'].sub(r'\1', text)
        
        text = self.patterns['underline'].sub(r'\1', text)
        
        text = self.patterns['strikethrough'].sub(r'[\1]', text)
        
        return text
    
    def _parse_links(self, text: str) -> str:
        """Parse links."""
        text = self.patterns['link'].sub(r'\1 (\2)', text)
        
        text = self.patterns['image'].sub(r'[Image: \1]', text)
        
        return text
    
    def _parse_inline_code(self, text: str) -> str:
        """Parse inline code."""
        return self.patterns['code_inline'].sub(r'[\1]', text)
    
    def _cleanup(self, text: str) -> str:
        """Clean up parsed text."""
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        text = text.strip()
        
        return text
    
    def extract_links(self, text: str) -> List[Dict[str, str]]:
        """
        Extract all links from markdown.
        
        Args:
            text: Markdown text
            
        Returns:
            List of link dictionaries
        """
        links = []
        
        for match in self.patterns['link'].finditer(text):
            links.append({
                'text': match.group(1),
                'url': match.group(2)
            })
        
        return links
    
    def extract_images(self, text: str) -> List[Dict[str, str]]:
        """
        Extract all images from markdown.
        
        Args:
            text: Markdown text
            
        Returns:
            List of image dictionaries
        """
        images = []
        
        for match in self.patterns['image'].finditer(text):
            images.append({
                'alt': match.group(1),
                'url': match.group(2)
            })
        
        return images
    
    def strip_markdown(self, text: str) -> str:
        """
        Remove all markdown formatting.
        
        Args:
            text: Markdown text
            
        Returns:
            Plain text
        """
        result = text
        
        for pattern in self.patterns.values():
            result = pattern.sub(r'\1', result)
        
        result = re.sub(r'[#\*_~`\[\]\(\)]', '', result)
        
        return result.strip()
    
    def to_html(self, text: str) -> str:
        """
        Convert markdown to HTML (basic).
        
        Args:
            text: Markdown text
            
        Returns:
            HTML text
        """
        result = text
        
        result = self.patterns['bold'].sub(r'<strong>\1</strong>', result)
        result = self.patterns['italic'].sub(r'<em>\1</em>', result)
        result = self.patterns['code_inline'].sub(r'<code>\1</code>', result)
        result = self.patterns['link'].sub(r'<a href="\2">\1</a>', result)
        
        result = result.replace('\n\n', '</p><p>')
        result = f'<p>{result}</p>'
        
        return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    parser = MarkdownParser()
    
    markdown_text = """
# Test Heading

This is **bold** and *italic* text.

- List item 1
- List item 2

Here is a [link](https://example.com).

def hello():
print("Hello World")

"""
    
    parsed = parser.parse(markdown_text)
    print(parsed)
    
    links = parser.extract_links(markdown_text)
    print(f"\nLinks: {links}")
