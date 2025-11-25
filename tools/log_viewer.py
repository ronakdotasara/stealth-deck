#!/usr/bin/env python3
"""
================================================================================
log_viewer.py - Log Analysis and Viewing Tool
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Interactive log viewer and analyzer for Stealth Deck logs.
Provides filtering, searching, and analysis capabilities.

Features:
- Log parsing
- Level filtering
- Keyword search
- Timeline analysis
- Error detection
- Export functionality

================================================================================
"""

import sys
import re
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Log entry data."""
    timestamp: datetime
    level: LogLevel
    module: str
    message: str
    line_number: int


class LogViewer:
    """
    Log viewer and analyzer.
    
    Parses and analyzes log files.
    """
    
    def __init__(self, log_file: str):
        """
        Initialize log viewer.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        self.entries: List[LogEntry] = []
        
        self.log_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s+'
            r'(\w+)\s+'
            r'\[([^\]]+)\]\s+'
            r'(.*)'
        )
    
    def load(self):
        """Load and parse log file."""
        print(f"Loading log file: {self.log_file}")
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            entry = self.parse_line(line.strip(), line_num)
            
            if entry:
                self.entries.append(entry)
        
        print(f"Loaded {len(self.entries)} log entries")
    
    def parse_line(self, line: str, line_num: int) -> Optional[LogEntry]:
        """
        Parse log line.
        
        Args:
            line: Log line
            line_num: Line number
            
        Returns:
            Log entry or None
        """
        match = self.log_pattern.match(line)
        
        if not match:
            return None
        
        timestamp_str, level_str, module, message = match.groups()
        
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            level = LogLevel(level_str)
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                module=module,
                message=message,
                line_number=line_num
            )
        
        except Exception:
            return None
    
    def filter_by_level(self, level: LogLevel) -> List[LogEntry]:
        """
        Filter entries by log level.
        
        Args:
            level: Log level to filter
            
        Returns:
            Filtered entries
        """
        return [e for e in self.entries if e.level == level]
    
    def filter_by_module(self, module: str) -> List[LogEntry]:
        """
        Filter entries by module.
        
        Args:
            module: Module name
            
        Returns:
            Filtered entries
        """
        return [e for e in self.entries if module.lower() in e.module.lower()]
    
    def search(self, keyword: str) -> List[LogEntry]:
        """
        Search for keyword in messages.
        
        Args:
            keyword: Search keyword
            
        Returns:
            Matching entries
        """
        keyword = keyword.lower()
        
        return [
            e for e in self.entries
            if keyword in e.message.lower()
        ]
    
    def get_errors(self) -> List[LogEntry]:
        """
        Get all error and critical entries.
        
        Returns:
            Error entries
        """
        return [
            e for e in self.entries
            if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]
        ]
    
    def get_timeline(self, interval_minutes: int = 5):
        """
        Get timeline of log entries.
        
        Args:
            interval_minutes: Time interval in minutes
            
        Returns:
            Timeline data
        """
        if not self.entries:
            return {}
        
        from collections import defaultdict
        
        timeline = defaultdict(int)
        
        start_time = self.entries[0].timestamp
        
        for entry in self.entries:
            delta = (entry.timestamp - start_time).total_seconds()
            interval = int(delta // (interval_minutes * 60))
            
            timeline[interval] += 1
        
        return dict(timeline)
    
    def get_statistics(self):
        """Get log statistics."""
        from collections import Counter
        
        level_counts = Counter(e.level for e in self.entries)
        module_counts = Counter(e.module for e in self.entries)
        
        return {
            'total_entries': len(self.entries),
            'level_counts': dict(level_counts),
            'module_counts': dict(module_counts),
            'error_count': level_counts[LogLevel.ERROR] + level_counts[LogLevel.CRITICAL],
            'time_range': (
                self.entries[0].timestamp if self.entries else None,
                self.entries[-1].timestamp if self.entries else None
            )
        }
    
    def print_entries(self, entries: List[LogEntry], limit: int = 50):
        """
        Print log entries.
        
        Args:
            entries: Entries to print
            limit: Maximum entries to print
        """
        if not entries:
            print("No entries found")
            return
        
        print(f"\nShowing {min(len(entries), limit)} of {len(entries)} entries:")
        print("-" * 100)
        
        for entry in entries[:limit]:
            timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            level_color = self.get_level_color(entry.level)
            
            print(f"{timestamp} {level_color}{entry.level.value:8}{self.RESET} "
                  f"[{entry.module:20}] {entry.message[:80]}")
        
        if len(entries) > limit:
            print(f"\n... and {len(entries) - limit} more entries")
        
        print("-" * 100)
    
    # ANSI color codes
    RESET = '\033[0m'
    
    def get_level_color(self, level: LogLevel) -> str:
        """Get color for log level."""
        colors = {
            LogLevel.DEBUG: '\033[36m',      # Cyan
            LogLevel.INFO: '\033[32m',       # Green
            LogLevel.WARNING: '\033[33m',    # Yellow
            LogLevel.ERROR: '\033[31m',      # Red
            LogLevel.CRITICAL: '\033[35m'    # Magenta
        }
        return colors.get(level, '')
    
    def interactive_mode(self):
        """Run interactive mode."""
        print("\nInteractive Log Viewer")
        print("=" * 100)
        
        while True:
            print("\nCommands:")
            print("  all - Show all entries")
            print("  errors - Show errors")
            print("  level <LEVEL> - Filter by level")
            print("  module <MODULE> - Filter by module")
            print("  search <KEYWORD> - Search messages")
            print("  stats - Show statistics")
            print("  timeline - Show timeline")
            print("  quit - Exit")
            print()
            
            command = input("Enter command: ").strip().lower()
            
            if command == 'quit':
                break
            
            elif command == 'all':
                self.print_entries(self.entries)
            
            elif command == 'errors':
                errors = self.get_errors()
                self.print_entries(errors)
            
            elif command.startswith('level '):
                level_str = command.split(' ', 1)[1].upper()
                try:
                    level = LogLevel(level_str)
                    entries = self.filter_by_level(level)
                    self.print_entries(entries)
                except ValueError:
                    print(f"Invalid level: {level_str}")
            
            elif command.startswith('module '):
                module = command.split(' ', 1)[1]
                entries = self.filter_by_module(module)
                self.print_entries(entries)
            
            elif command.startswith('search '):
                keyword = command.split(' ', 1)[1]
                entries = self.search(keyword)
                self.print_entries(entries)
            
            elif command == 'stats':
                self.print_statistics()
            
            elif command == 'timeline':
                self.print_timeline()
            
            else:
                print("Unknown command")
    
    def print_statistics(self):
        """Print log statistics."""
        stats = self.get_statistics()
        
        print("\nLog Statistics")
        print("=" * 100)
        print(f"Total Entries: {stats['total_entries']}")
        print()
        
        print("Entries by Level:")
        for level, count in stats['level_counts'].items():
            percentage = (count / stats['total_entries'] * 100) if stats['total_entries'] > 0 else 0
            print(f"  {level.value:10s}: {count:6d} ({percentage:5.1f}%)")
        
        print()
        print("Top 10 Modules:")
        sorted_modules = sorted(stats['module_counts'].items(), key=lambda x: x[1], reverse=True)
        for module, count in sorted_modules[:10]:
            print(f"  {module:30s}: {count:6d}")
        
        if stats['time_range'][0]:
            print()
            print(f"Time Range: {stats['time_range'][0]} to {stats['time_range'][1]}")
            duration = stats['time_range'][1] - stats['time_range'][0]
            print(f"Duration: {duration}")
        
        print("=" * 100)
    
    def print_timeline(self):
        """Print timeline."""
        timeline = self.get_timeline(5)
        
        print("\nLog Timeline (5-minute intervals)")
        print("=" * 100)
        
        max_count = max(timeline.values()) if timeline else 1
        
        for interval, count in sorted(timeline.items()):
            bar_length = int((count / max_count) * 50)
            bar = '█' * bar_length
            
            print(f"Interval {interval:3d}: {bar} {count}")
        
        print("=" * 100)
    
    def export_filtered(self, entries: List[LogEntry], output_file: str):
        """
        Export filtered entries.
        
        Args:
            entries: Entries to export
            output_file: Output filename
        """
        with open(output_file, 'w') as f:
            for entry in entries:
                timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
                f.write(f"{timestamp} {entry.level.value} [{entry.module}] {entry.message}\n")
        
        print(f"Exported {len(entries)} entries to {output_file}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: log_viewer.py <log_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    viewer = LogViewer(log_file)
    
    try:
        viewer.load()
    except FileNotFoundError:
        print(f"Error: Log file not found: {log_file}")
        sys.exit(1)
    
    viewer.interactive_mode()


if __name__ == '__main__':
    main()
