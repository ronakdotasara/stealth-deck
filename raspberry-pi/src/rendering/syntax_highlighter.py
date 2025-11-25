"""
================================================================================
syntax_highlighter.py - Code Syntax Highlighter
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Syntax highlighting for code snippets in AI responses.
Converts code to display-friendly format with annotations.

Features:
- Multiple language support
- Token-based highlighting
- Theme support
- Line numbering
- Display optimization

================================================================================
"""

import logging
import re
from typing import List, Dict, Optional
from enum import Enum


class TokenType(Enum):
    """Token types for syntax highlighting."""
    KEYWORD = 'keyword'
    STRING = 'string'
    COMMENT = 'comment'
    NUMBER = 'number'
    OPERATOR = 'operator'
    IDENTIFIER = 'identifier'
    FUNCTION = 'function'
    CLASS = 'class'


class SyntaxHighlighter:
    """
    Syntax highlighter for code snippets.
    
    Provides basic syntax highlighting for display.
    """
    
    def __init__(self):
        """Initialize syntax highlighter."""
        self.logger = logging.getLogger('syntax_highlighter')
        
        self.languages = {
            'python': self._highlight_python,
            'cpp': self._highlight_cpp,
            'c': self._highlight_c,
            'javascript': self._highlight_javascript,
            'bash': self._highlight_bash
        }
        
        self.python_keywords = [
            'def', 'class', 'if', 'else', 'elif', 'for', 'while',
            'return', 'import', 'from', 'as', 'try', 'except',
            'finally', 'with', 'lambda', 'yield', 'pass', 'break',
            'continue', 'and', 'or', 'not', 'in', 'is', 'None',
            'True', 'False', 'async', 'await'
        ]
        
        self.cpp_keywords = [
            'int', 'float', 'double', 'char', 'void', 'bool',
            'if', 'else', 'for', 'while', 'do', 'switch', 'case',
            'return', 'break', 'continue', 'class', 'struct',
            'public', 'private', 'protected', 'virtual', 'static',
            'const', 'new', 'delete', 'true', 'false', 'nullptr'
        ]
    
    def highlight(self, code: str, language: str = 'python',
                 line_numbers: bool = False) -> List[str]:
        """
        Highlight code snippet.
        
        Args:
            code: Code to highlight
            language: Programming language
            line_numbers: Add line numbers
            
        Returns:
            List of formatted lines
        """
        try:
            language = language.lower()
            
            if language not in self.languages:
                self.logger.warning(f"Language {language} not supported")
                return self._format_plain(code, line_numbers)
            
            highlighter = self.languages[language]
            
            highlighted = highlighter(code)
            
            if line_numbers:
                highlighted = self._add_line_numbers(highlighted)
            
            return highlighted
            
        except Exception as e:
            self.logger.error(f"Highlighting failed: {e}")
            return self._format_plain(code, line_numbers)
    
    def _highlight_python(self, code: str) -> List[str]:
        """Highlight Python code."""
        lines = code.split('\n')
        highlighted = []
        
        for line in lines:
            formatted = line
            
            # Comments
            if '#' in line:
                parts = line.split('#', 1)
                formatted = parts[0] + f"# {parts[1]}"  # Mark comment
            
            # Keywords
            for keyword in self.python_keywords:
                pattern = r'\b' + keyword + r'\b'
                formatted = re.sub(pattern, f"[{keyword}]", formatted)
            
            # Strings
            formatted = re.sub(r'"([^"]*)"', r'"\1"', formatted)
            formatted = re.sub(r"'([^']*)'", r"'\1'", formatted)
            
            highlighted.append(formatted)
        
        return highlighted
    
    def _highlight_cpp(self, code: str) -> List[str]:
        """Highlight C++ code."""
        lines = code.split('\n')
        highlighted = []
        
        for line in lines:
            formatted = line
            
            # Comments
            if '//' in line:
                parts = line.split('//', 1)
                formatted = parts[0] + f"// {parts[1]}"
            
            # Keywords
            for keyword in self.cpp_keywords:
                pattern = r'\b' + keyword + r'\b'
                formatted = re.sub(pattern, f"[{keyword}]", formatted)
            
            highlighted.append(formatted)
        
        return highlighted
    
    def _highlight_c(self, code: str) -> List[str]:
        """Highlight C code."""
        return self._highlight_cpp(code)
    
    def _highlight_javascript(self, code: str) -> List[str]:
        """Highlight JavaScript code."""
        js_keywords = ['var', 'let', 'const', 'function', 'if', 'else',
                      'for', 'while', 'return', 'true', 'false', 'null']
        
        lines = code.split('\n')
        highlighted = []
        
        for line in lines:
            formatted = line
            
            for keyword in js_keywords:
                pattern = r'\b' + keyword + r'\b'
                formatted = re.sub(pattern, f"[{keyword}]", formatted)
            
            highlighted.append(formatted)
        
        return highlighted
    
    def _highlight_bash(self, code: str) -> List[str]:
        """Highlight Bash code."""
        lines = code.split('\n')
        highlighted = []
        
        for line in lines:
            formatted = line
            
            # Comments
            if '#' in line and not line.strip().startswith('#!'):
                parts = line.split('#', 1)
                formatted = parts[0] + f"# {parts[1]}"
            
            highlighted.append(formatted)
        
        return highlighted
    
    def _format_plain(self, code: str, line_numbers: bool) -> List[str]:
        """Format code without highlighting."""
        lines = code.split('\n')
        
        if line_numbers:
            lines = self._add_line_numbers(lines)
        
        return lines
    
    def _add_line_numbers(self, lines: List[str]) -> List[str]:
        """Add line numbers to code."""
        max_digits = len(str(len(lines)))
        
        numbered = []
        
        for i, line in enumerate(lines, 1):
            line_num = str(i).rjust(max_digits)
            numbered.append(f"{line_num} | {line}")
        
        return numbered
    
    def detect_language(self, code: str) -> str:
        """
        Detect programming language from code.
        
        Args:
            code: Code snippet
            
        Returns:
            Detected language
        """
        if 'def ' in code or 'import ' in code:
            return 'python'
        
        if '#include' in code or 'int main' in code:
            return 'cpp'
        
        if 'function' in code or 'var ' in code:
            return 'javascript'
        
        if code.strip().startswith('#!'):
            return 'bash'
        
        return 'plain'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    highlighter = SyntaxHighlighter()
    
    test_code = """
def hello():
    print("Hello World")
    return True
"""
    
    result = highlighter.highlight(test_code, 'python', line_numbers=True)
    
    for line in result:
        print(line)
