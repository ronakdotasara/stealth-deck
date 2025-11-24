"""
================================================================================
notes_manager.py - Encrypted Notes Manager for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Manages encrypted notes storage with AES-256-GCM encryption.
Provides secure storage for sensitive information.

Features:
- AES-256-GCM encryption
- Note creation, editing, deletion
- Search functionality
- Categorization
- Export/import

================================================================================
"""

import logging
import json
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets


class Note:
    """Represents a single note."""
    
    def __init__(self, title: str, content: str, category: str = "general"):
        """
        Initialize note.
        
        Args:
            title: Note title
            content: Note content
            category: Note category
        """
        self.id = secrets.token_hex(8)
        self.title = title
        self.content = content
        self.category = category
        self.created_at = datetime.now().isoformat()
        self.modified_at = self.created_at
        self.tags: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert note to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """Create note from dictionary."""
        note = cls(data['title'], data['content'], data.get('category', 'general'))
        note.id = data['id']
        note.created_at = data['created_at']
        note.modified_at = data['modified_at']
        note.tags = data.get('tags', [])
        return note


class NotesManager:
    """
    Encrypted notes manager.
    
    Manages encrypted note storage and retrieval.
    """
    
    def __init__(self, notes_dir: str, encryption_key: bytes):
        """
        Initialize notes manager.
        
        Args:
            notes_dir: Directory for storing notes
            encryption_key: 32-byte encryption key
        """
        self.notes_dir = Path(notes_dir)
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        
        self.encryption_key = encryption_key
        self.aesgcm = AESGCM(encryption_key)
        
        self.logger = logging.getLogger('notes_manager')
        
        self.notes: List[Note] = []
        self.current_index = 0
        
        self._load_all_notes()
    
    def create_note(self, title: str, content: str, category: str = "general") -> Note:
        """
        Create new note.
        
        Args:
            title: Note title
            content: Note content
            category: Note category
            
        Returns:
            Created note
        """
        note = Note(title, content, category)
        
        self._save_note(note)
        
        self.notes.append(note)
        
        self.logger.info(f"Note created: {note.id}")
        
        return note
    
    def get_note(self, note_id: str) -> Optional[Note]:
        """
        Get note by ID.
        
        Args:
            note_id: Note ID
            
        Returns:
            Note or None
        """
        for note in self.notes:
            if note.id == note_id:
                return note
        return None
    
    def update_note(self, note_id: str, title: Optional[str] = None, 
                   content: Optional[str] = None) -> bool:
        """
        Update existing note.
        
        Args:
            note_id: Note ID
            title: New title (optional)
            content: New content (optional)
            
        Returns:
            True if updated
        """
        note = self.get_note(note_id)
        
        if not note:
            return False
        
        if title is not None:
            note.title = title
        
        if content is not None:
            note.content = content
        
        note.modified_at = datetime.now().isoformat()
        
        self._save_note(note)
        
        self.logger.info(f"Note updated: {note_id}")
        
        return True
    
    def delete_note(self, note_id: str) -> bool:
        """
        Delete note.
        
        Args:
            note_id: Note ID
            
        Returns:
            True if deleted
        """
        note = self.get_note(note_id)
        
        if not note:
            return False
        
        note_file = self._get_note_path(note_id)
        
        if note_file.exists():
            note_file.unlink()
        
        self.notes = [n for n in self.notes if n.id != note_id]
        
        self.logger.info(f"Note deleted: {note_id}")
        
        return True
    
    def list_notes(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all notes.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of note summaries
        """
        notes_list = self.notes
        
        if category:
            notes_list = [n for n in notes_list if n.category == category]
        
        return [{
            'id': n.id,
            'title': n.title,
            'category': n.category,
            'created_at': n.created_at,
            'modified_at': n.modified_at
        } for n in notes_list]
    
    def search_notes(self, query: str) -> List[Note]:
        """
        Search notes by title or content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching notes
        """
        query_lower = query.lower()
        
        results = []
        for note in self.notes:
            if (query_lower in note.title.lower() or 
                query_lower in note.content.lower()):
                results.append(note)
        
        return results
    
    def get_current(self) -> Optional[Note]:
        """
        Get currently selected note.
        
        Returns:
            Current note or None
        """
        if 0 <= self.current_index < len(self.notes):
            return self.notes[self.current_index]
        return None
    
    def next(self) -> Optional[Note]:
        """
        Move to next note.
        
        Returns:
            Next note or None
        """
        if len(self.notes) > 0:
            self.current_index = (self.current_index + 1) % len(self.notes)
            return self.notes[self.current_index]
        return None
    
    def previous(self) -> Optional[Note]:
        """
        Move to previous note.
        
        Returns:
            Previous note or None
        """
        if len(self.notes) > 0:
            self.current_index = (self.current_index - 1) % len(self.notes)
            return self.notes[self.current_index]
        return None
    
    def add_tag(self, note_id: str, tag: str) -> bool:
        """
        Add tag to note.
        
        Args:
            note_id: Note ID
            tag: Tag to add
            
        Returns:
            True if added
        """
        note = self.get_note(note_id)
        
        if not note:
            return False
        
        if tag not in note.tags:
            note.tags.append(tag)
            self._save_note(note)
        
        return True
    
    def get_categories(self) -> List[str]:
        """
        Get all note categories.
        
        Returns:
            List of categories
        """
        categories = set(note.category for note in self.notes)
        return sorted(list(categories))
    
    def export_notes(self, export_path: str) -> bool:
        """
        Export all notes to JSON file.
        
        Args:
            export_path: Path to export file
            
        Returns:
            True if exported
        """
        try:
            export_data = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'notes': [note.to_dict() for note in self.notes]
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Notes exported to: {export_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def _save_note(self, note: Note) -> None:
        """
        Save note to encrypted file.
        
        Args:
            note: Note to save
        """
        try:
            note_data = json.dumps(note.to_dict()).encode()
            
            nonce = secrets.token_bytes(12)
            
            encrypted_data = self.aesgcm.encrypt(nonce, note_data, None)
            
            note_file = self._get_note_path(note.id)
            
            with open(note_file, 'wb') as f:
                f.write(nonce + encrypted_data)
            
            note_file.chmod(0o600)
            
        except Exception as e:
            self.logger.error(f"Failed to save note {note.id}: {e}")
    
    def _load_note(self, note_id: str) -> Optional[Note]:
        """
        Load note from encrypted file.
        
        Args:
            note_id: Note ID
            
        Returns:
            Loaded note or None
        """
        try:
            note_file = self._get_note_path(note_id)
            
            if not note_file.exists():
                return None
            
            with open(note_file, 'rb') as f:
                data = f.read()
            
            nonce = data[:12]
            encrypted_data = data[12:]
            
            decrypted_data = self.aesgcm.decrypt(nonce, encrypted_data, None)
            
            note_dict = json.loads(decrypted_data.decode())
            
            return Note.from_dict(note_dict)
            
        except Exception as e:
            self.logger.error(f"Failed to load note {note_id}: {e}")
            return None
    
    def _load_all_notes(self) -> None:
        """Load all notes from disk."""
        try:
            note_files = self.notes_dir.glob('*.enc')
            
            for note_file in note_files:
                note_id = note_file.stem
                note = self._load_note(note_id)
                
                if note:
                    self.notes.append(note)
            
            self.notes.sort(key=lambda n: n.modified_at, reverse=True)
            
            self.logger.info(f"Loaded {len(self.notes)} notes")
            
        except Exception as e:
            self.logger.error(f"Failed to load notes: {e}")
    
    def _get_note_path(self, note_id: str) -> Path:
        """
        Get file path for note.
        
        Args:
            note_id: Note ID
            
        Returns:
            Path to note file
        """
        return self.notes_dir / f"{note_id}.enc"


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    import secrets
    
    key = secrets.token_bytes(32)
    
    manager = NotesManager('/tmp/test_notes', key)
    
    note = manager.create_note(
        "Test Note",
        "This is a test note with encrypted content.",
        "test"
    )
    
    print(f"Created note: {note.id}")
    
    notes = manager.list_notes()
    print(f"Total notes: {len(notes)}")
    
    search_results = manager.search_notes("test")
    print(f"Search results: {len(search_results)}")
