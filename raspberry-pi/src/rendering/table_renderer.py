"""
================================================================================
table_renderer.py - Table Renderer for Display
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Renders tables for small display output.
Handles column sizing, alignment, and text wrapping.

Features:
- Auto column sizing
- Text wrapping
- Multiple alignment options
- Border styles
- Header/footer support

================================================================================
"""

import logging
from typing import List, Dict, Optional
from enum import Enum


class Alignment(Enum):
    """Text alignment options."""
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'


class BorderStyle(Enum):
    """Table border styles."""
    NONE = 'none'
    SIMPLE = 'simple'
    DOUBLE = 'double'
    ASCII = 'ascii'


class TableRenderer:
    """
    Table renderer for display output.
    
    Formats tabular data for small displays.
    """
    
    def __init__(self, max_width: int = 40):
        """
        Initialize table renderer.
        
        Args:
            max_width: Maximum table width
        """
        self.logger = logging.getLogger('table_renderer')
        
        self.max_width = max_width
        self.default_alignment = Alignment.LEFT
        self.border_style = BorderStyle.SIMPLE
    
    def render(self, headers: List[str], rows: List[List[str]],
              alignments: Optional[List[Alignment]] = None) -> List[str]:
        """
        Render table.
        
        Args:
            headers: Column headers
            rows: Table rows
            alignments: Column alignments
            
        Returns:
            List of formatted lines
        """
        try:
            if not headers or not rows:
                return []
            
            num_cols = len(headers)
            
            if alignments is None:
                alignments = [self.default_alignment] * num_cols
            
            col_widths = self._calculate_column_widths(headers, rows)
            
            lines = []
            
            if self.border_style != BorderStyle.NONE:
                lines.append(self._render_border_top(col_widths))
            
            lines.append(self._render_row(headers, col_widths, alignments, is_header=True))
            
            if self.border_style != BorderStyle.NONE:
                lines.append(self._render_border_separator(col_widths))
            
            for row in rows:
                lines.append(self._render_row(row, col_widths, alignments))
            
            if self.border_style != BorderStyle.NONE:
                lines.append(self._render_border_bottom(col_widths))
            
            return lines
            
        except Exception as e:
            self.logger.error(f"Table rendering failed: {e}")
            return []
    
    def _calculate_column_widths(self, headers: List[str], 
                                 rows: List[List[str]]) -> List[int]:
        """Calculate optimal column widths."""
        num_cols = len(headers)
        
        max_widths = [len(h) for h in headers]
        
        for row in rows:
            for i, cell in enumerate(row[:num_cols]):
                max_widths[i] = max(max_widths[i], len(str(cell)))
        
        total_width = sum(max_widths) + (num_cols - 1) * 3 + 4
        
        if total_width > self.max_width:
            max_widths = self._adjust_widths(max_widths, num_cols)
        
        return max_widths
    
    def _adjust_widths(self, widths: List[int], num_cols: int) -> List[int]:
        """Adjust column widths to fit max width."""
        available = self.max_width - (num_cols - 1) * 3 - 4
        
        min_width = 3
        
        for i in range(len(widths)):
            widths[i] = max(min_width, min(widths[i], available // num_cols))
        
        return widths
    
    def _render_row(self, cells: List[str], widths: List[int],
                   alignments: List[Alignment], is_header: bool = False) -> str:
        """Render table row."""
        formatted_cells = []
        
        for i, cell in enumerate(cells):
            width = widths[i] if i < len(widths) else 10
            alignment = alignments[i] if i < len(alignments) else self.default_alignment
            
            formatted = self._format_cell(str(cell), width, alignment)
            formatted_cells.append(formatted)
        
        if self.border_style != BorderStyle.NONE:
            return '| ' + ' | '.join(formatted_cells) + ' |'
        else:
            return ' '.join(formatted_cells)
    
    def _format_cell(self, text: str, width: int, alignment: Alignment) -> str:
        """Format cell content."""
        if len(text) > width:
            text = text[:width-2] + '..'
        
        if alignment == Alignment.LEFT:
            return text.ljust(width)
        elif alignment == Alignment.CENTER:
            return text.center(width)
        elif alignment == Alignment.RIGHT:
            return text.rjust(width)
        
        return text
    
    def _render_border_top(self, widths: List[int]) -> str:
        """Render top border."""
        if self.border_style == BorderStyle.SIMPLE:
            parts = ['-' * w for w in widths]
            return '+-' + '-+-'.join(parts) + '-+'
        
        return ''
    
    def _render_border_separator(self, widths: List[int]) -> str:
        """Render separator border."""
        if self.border_style == BorderStyle.SIMPLE:
            parts = ['-' * w for w in widths]
            return '+-' + '-+-'.join(parts) + '-+'
        
        return ''
    
    def _render_border_bottom(self, widths: List[int]) -> str:
        """Render bottom border."""
        if self.border_style == BorderStyle.SIMPLE:
            parts = ['-' * w for w in widths]
            return '+-' + '-+-'.join(parts) + '-+'
        
        return ''
    
    def render_dict_table(self, data: List[Dict[str, str]]) -> List[str]:
        """
        Render table from list of dictionaries.
        
        Args:
            data: List of dictionaries
            
        Returns:
            Formatted lines
        """
        if not data:
            return []
        
        headers = list(data[0].keys())
        
        rows = [[str(item.get(key, '')) for key in headers] for item in data]
        
        return self.render(headers, rows)
    
    def render_key_value(self, data: Dict[str, str]) -> List[str]:
        """
        Render key-value pairs.
        
        Args:
            data: Dictionary of key-value pairs
            
        Returns:
            Formatted lines
        """
        headers = ['Key', 'Value']
        
        rows = [[str(k), str(v)] for k, v in data.items()]
        
        return self.render(headers, rows)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    renderer = TableRenderer(max_width=50)
    
    # Test data
    headers = ['Name', 'Age', 'City']
    rows = [
        ['Alice', '30', 'NYC'],
        ['Bob', '25', 'LA'],
        ['Charlie', '35', 'Chicago']
    ]
    
    lines = renderer.render(headers, rows)
    
    for line in lines:
        print(line)
