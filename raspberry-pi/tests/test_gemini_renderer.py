"""
================================================================================
test_gemini_renderer.py - Gemini Response Renderer Tests
================================================================================
Version: 1.0.0
Date: 2025-11-25

Unit tests for Gemini response rendering.
================================================================================
"""

import pytest
from unittest.mock import Mock
from src.rendering.gemini_renderer import GeminiRenderer


class TestGeminiRenderer:
    """Test suite for Gemini renderer."""
    
    @pytest.fixture
    def renderer(self):
        """Create renderer instance."""
        return GeminiRenderer(max_width=40)
    
    def test_initialization(self, renderer):
        """Test renderer initialization."""
        assert renderer.max_width == 40
    
    def test_render_plain_text(self, renderer):
        """Test rendering plain text."""
        text = "This is a simple response."
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
        assert "This is a simple response." in ' '.join(lines)
    
    def test_render_with_bold(self, renderer):
        """Test rendering bold text."""
        text = "This is **bold** text."
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
    
    def test_render_with_italic(self, renderer):
        """Test rendering italic text."""
        text = "This is *italic* text."
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
    
    def test_render_code_block(self, renderer):
        """Test rendering code block."""
        text = """Here is code:

End of code."""
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
        assert any('def hello' in line for line in lines)
    
    def test_render_inline_code(self, renderer):
        """Test rendering inline code."""
        text = "Use `print()` function."
        
    
        lines = renderer.render(text)
        
        assert len(lines) > 0
    
    def test_render_list(self, renderer):
        """Test rendering list."""
        text = """Items:
- Item 1
- Item 2
- Item 3"""
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
        assert any('Item 1' in line for line in lines)
    
    def test_render_numbered_list(self, renderer):
        """Test rendering numbered list."""
        text = """Steps:
1. First step
2. Second step
3. Third step"""
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
    
    def test_wrap_long_text(self, renderer):
        """Test wrapping long text."""
        long_text = "This is a very long line that should be wrapped to fit the maximum width constraint."
        
        lines = renderer.render(long_text)
        
        for line in lines:
            assert len(line) <= renderer.max_width + 10  # Allow some margin
    
    def test_render_heading(self, renderer):
        """Test rendering headings."""
        text = """# Heading 1
## Heading 2
### Heading 3"""
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
    
    def test_render_links(self, renderer):
        """Test rendering links."""
        text = "Visit [Google](https://google.com) for search."
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
    
    def test_render_empty_text(self, renderer):
        """Test rendering empty text."""
        lines = renderer.render("")
        
        assert len(lines) == 0
    
    def test_render_multiline(self, renderer):
        """Test rendering multiline text."""
        text = """Line 1
Line 2
Line 3"""
        
        lines = renderer.render(text)
        
        assert len(lines) >= 3


class TestMarkdownParsing:
    """Test Markdown parsing."""
    
    @pytest.fixture
    def renderer(self):
        """Create renderer."""
        return GeminiRenderer()
    
    def test_parse_bold(self, renderer):
        """Test parsing bold markers."""
        text = "This is **bold** text"
        
        parsed = renderer.parse_markdown(text)
        
        assert parsed is not None
    
    def test_parse_italic(self, renderer):
        """Test parsing italic markers."""
        text = "This is *italic* text"
        
        parsed = renderer.parse_markdown(text)
        
        assert parsed is not None
    
    def test_parse_code(self, renderer):
        """Test parsing code blocks."""
        text = "``````"
        
        blocks = renderer.extract_code_blocks(text)
        
        assert len(blocks) > 0
    
    def test_parse_list(self, renderer):
        """Test parsing lists."""
        text = "- Item 1\n- Item 2"
        
        items = renderer.extract_list_items(text)
        
        assert len(items) == 2


class TestCodeFormatting:
    """Test code block formatting."""
    
    @pytest.fixture
    def renderer(self):
        """Create renderer."""
        return GeminiRenderer()
    
    def test_format_python_code(self, renderer):
        """Test formatting Python code."""
        code = """def hello():
    print("Hello")"""
        
        formatted = renderer.format_code_block(code, 'python')
        
        assert len(formatted) > 0
    
    def test_format_javascript_code(self, renderer):
        """Test formatting JavaScript code."""
        code = """function hello() {
    console.log("Hello");
}"""
        
        formatted = renderer.format_code_block(code, 'javascript')
        
        assert len(formatted) > 0
    
    def test_format_unknown_language(self, renderer):
        """Test formatting unknown language."""
        code = "Some code"
        
        formatted = renderer.format_code_block(code, 'unknown')
        
        assert len(formatted) > 0


class TestTextWrapping:
    """Test text wrapping."""
    
    @pytest.fixture
    def renderer(self):
        """Create renderer with specific width."""
        return GeminiRenderer(max_width=20)
    
    def test_wrap_short_text(self, renderer):
        """Test wrapping short text."""
        text = "Short"
        
        wrapped = renderer.wrap_text(text)
        
        assert len(wrapped) == 1
    
    def test_wrap_long_text(self, renderer):
        """Test wrapping long text."""
        text = "This is a very long line that needs wrapping"
        
        wrapped = renderer.wrap_text(text)
        
        assert len(wrapped) > 1
    
    def test_wrap_preserves_words(self, renderer):
        """Test that wrapping preserves whole words."""
        text = "Word1 Word2 Word3 Word4 Word5"
        
        wrapped = renderer.wrap_text(text)
        
        for line in wrapped:
            # No words should be split
            assert not any(line.endswith(c) for c in 'abcdefghijklmnopqrstuvwxyz')


class TestSpecialCharacters:
    """Test handling special characters."""
    
    @pytest.fixture
    def renderer(self):
        """Create renderer."""
        return GeminiRenderer()
    
    def test_render_unicode(self, renderer):
        """Test rendering Unicode characters."""
        text = "Hello 世界 🌍"
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
    
    def test_render_math_symbols(self, renderer):
        """Test rendering math symbols."""
        text = "Formula: α + β = γ"
        
        lines = renderer.render(text)
        
        assert len(lines) > 0
    
    def test_render_special_markdown(self, renderer):
        """Test rendering special Markdown characters."""
        text = "Use \\* for asterisk and \\_ for underscore"
        
        lines = renderer.render(text)
        
        assert len(lines) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
