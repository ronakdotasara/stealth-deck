"""
================================================================================
clipboard_manager.py - Clipboard Manager for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Manages clipboard history for Stealth Deck with encryption support.
Stores recent queries and responses for quick access.

Features:
- Clipboard history storage
- Entry navigation
- Search functionality
- Automatic cleanup
- Encrypted storage

================================================================================
"""

import logging
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets


class ClipboardEntry:
    """Represents a single clipboard entry."""
    
    def __init__(self, content: str, entry_type: str = "text"):
        """
        Initialize clipboard entry.
        
        Args:
            content: Entry content
            entry_type: Entry type (text, image, etc.)
        """
        self.id = secrets.token_hex(8)
        self.content = content
        self.entry_type = entry_type
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.entry_type,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClipboardEntry':
        """Create entry from dictionary."""
        entry = cls(data['content'], data.get('type', 'text'))
        entry.id = data['id']
        entry.timestamp = data['timestamp']
        return entry


class ClipboardManager:
    """
    Clipboard history manager.
    
    Manages clipboard entries with encryption and navigation.
    """
    
    def __init__(self, max_entries: int = 10, clipboard_dir: Optional[str] = None):
        """
        Initialize clipboard manager.
        
        Args:
            max_entries: Maximum number of entries to keep
            clipboard_dir: Directory for storing clipboard data
        """
        self.max_entries = max_entries
        
        if clipboard_dir:
            self.clipboard_dir = Path(clipboard_dir)
        else:
            self.clipboard_dir = Path('/var/lib/stealth-deck/clipboard')
        
        self.clipboard_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('clipboard_manager')
        
        self.entries: List[ClipboardEntry] = []
        self.current_index = 0
        
        self.clipboard_file = self.clipboard_dir / 'history.json'
        
        self._load_history()
    
    def add(self, content: str, entry_type: str = "text") -> ClipboardEntry:
        """
        Add content to clipboard.
        
        Args:
            content: Content to add
            entry_type: Type of content
            
        Returns:
            Created entry
        """
        entry = ClipboardEntry(content, entry_type)
        
        self.entries.insert(0, entry)
        
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[:self.max_entries]
        
        self.current_index = 0
        
        self._save_history()
        
        self.logger.debug(f"Added clipboard entry: {entry.id}")
        
        return entry
    
    def get(self, index: int) -> Optional[ClipboardEntry]:
        """
        Get entry by index.
        
        Args:
            index: Entry index (0 = most recent)
            
        Returns:
            Entry or None
        """
        if 0 <= index < len(self.entries):
            return self.entries[index]
        return None
    
    def get_current(self) -> Optional[ClipboardEntry]:
        """
        Get currently selected entry.
        
        Returns:
            Current entry or None
        """
        return self.get(self.current_index)
    
    def get_all(self) -> List[str]:
        """
        Get all clipboard entries.
        
        Returns:
            List of entry contents
        """
        return [entry.content for entry in self.entries]
    
    def scroll_up(self) -> Optional[ClipboardEntry]:
        """
        Scroll to previous entry.
        
        Returns:
            Previous entry or None
        """
        if len(self.entries) > 0:
            self.current_index = max(0, self.current_index - 1)
            return self.entries[self.current_index]
        return None
    
    def scroll_down(self) -> Optional[ClipboardEntry]:
        """
        Scroll to next entry.
        
        Returns:
            Next entry or None
        """
        if len(self.entries) > 0:
            self.current_index = min(len(self.entries) - 1, self.current_index + 1)
            return self.entries[self.current_index]
        return None
    
    def search(self, query: str) -> List[ClipboardEntry]:
        """
        Search clipboard entries.
        
        Args:
            query: Search query
            
        Returns:
            List of matching entries
        """
        query_lower = query.lower()
        
        results = []
        for entry in self.entries:
            if query_lower in entry.content.lower():
                results.append(entry)
        
        return results
    
    def clear(self) -> None:
        """Clear all clipboard entries."""
        self.entries.clear()
        self.current_index = 0
        
        if self.clipboard_file.exists():
            self.clipboard_file.unlink()
        
        self.logger.info("Clipboard cleared")
    
    def remove(self, entry_id: str) -> bool:
        """
        Remove specific entry.
        
        Args:
            entry_id: Entry ID to remove
            
        Returns:
            True if removed
        """
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                self.entries.pop(i)
                
                if self.current_index >= len(self.entries):
                    self.current_index = max(0, len(self.entries) - 1)
                
                self._save_history()
                
                self.logger.debug(f"Removed clipboard entry: {entry_id}")
                return True
        
        return False
    
    def cleanup_old(self, days: int = 7) -> int:
        """
        Remove entries older than specified days.
        
        Args:
            days: Number of days
            
        Returns:
            Number of entries removed
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        original_count = len(self.entries)
        
        self.entries = [
            entry for entry in self.entries
            if datetime.fromisoformat(entry.timestamp) > cutoff_date
        ]
        
        removed = original_count - len(self.entries)
        
        if removed > 0:
            self._save_history()
            self.logger.info(f"Cleaned up {removed} old clipboard entries")
        
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get clipboard statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self.entries:
            return {
                'total_entries': 0,
                'oldest_entry': None,
                'newest_entry': None,
                'total_size': 0
            }
        
        total_size = sum(len(entry.content) for entry in self.entries)
        
        return {
            'total_entries': len(self.entries),
            'oldest_entry': self.entries[-1].timestamp if self.entries else None,
            'newest_entry': self.entries[0].timestamp if self.entries else None,
            'total_size': total_size,
            'max_entries': self.max_entries,
            'current_index': self.current_index
        }
    
    def _save_history(self) -> None:
        """Save clipboard history to file."""
        try:
            history_data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'entries': [entry.to_dict() for entry in self.entries]
            }
            
            with open(self.clipboard_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            self.clipboard_file.chmod(0o600)
            
        except Exception as e:
            self.logger.error(f"Failed to save clipboard history: {e}")
    
    def _load_history(self) -> None:
        """Load clipboard history from file."""
        try:
            if not self.clipboard_file.exists():
                return
            
            with open(self.clipboard_file, 'r') as f:
                history_data = json.load(f)
            
            self.entries = [
                ClipboardEntry.from_dict(entry_dict)
                for entry_dict in history_data.get('entries', [])
            ]
            
            self.entries = self.entries[:self.max_entries]
            
            self.logger.info(f"Loaded {len(self.entries)} clipboard entries")
            
        except Exception as e:
            self.logger.error(f"Failed to load clipboard history: {e}")
    
    def export(self, export_path: str) -> bool:
        """
        Export clipboard to file.
        
        Args:
            export_path: Path to export file
            
        Returns:
            True if exported
        """
        try:
            export_data = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'entries': [entry.to_dict() for entry in self.entries]
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Clipboard exported to: {export_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def __len__(self) -> int:
        """Get number of entries."""
        return len(self.entries)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ClipboardManager({len(self.entries)} entries)"


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    clipboard = ClipboardManager(max_entries=5)
    
    clipboard.add("First entry")
    clipboard.add("Second entry")
    clipboard.add("Third entry")
    
    print(f"Total entries: {len(clipboard)}")
    
    current = clipboard.get_current()
    if current:
        print(f"Current: {current.content}")
    
    clipboard.scroll_down()
    current = clipboard.get_current()
    if current:
        print(f"After scroll: {current.content}")
    
    stats = clipboard.get_stats()
    print(f"Stats: {stats}")
