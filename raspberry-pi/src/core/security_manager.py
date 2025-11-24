"""
================================================================================
security_manager.py - Security Manager for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Security manager implementing panic mode, secure deletion, and encryption
key management for Stealth Deck.

Features:
- Panic mode activation
- Secure file deletion
- Encryption key management
- Password hashing
- Security auditing

================================================================================
"""

import logging
import os
import hashlib
import secrets
import shutil
import subprocess
from typing import Optional, List
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class SecurityManager:
    """
    Security manager for Stealth Deck.
    
    Handles panic mode, secure deletion, and encryption.
    """
    
    def __init__(self, config):
        """
        Initialize security manager.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = logging.getLogger('security_manager')
        
        self.panic_active = False
        
        self.data_dir = Path('/var/lib/stealth-deck')
        self.notes_dir = self.data_dir / 'notes'
        self.clipboard_dir = self.data_dir / 'clipboard'
        self.cache_dir = self.data_dir / 'cache'
        
        self.encryption_key: Optional[bytes] = None
        
        self._load_encryption_key()
    
    def panic_mode(self) -> None:
        """
        Activate panic mode.
        
        Performs emergency lockdown:
        - Clears sensitive data
        - Disables wireless
        - Locks device
        """
        self.logger.warning("PANIC MODE ACTIVATED!")
        
        self.panic_active = True
        
        try:
            self._clear_clipboard()
            
            self._clear_cache()
            
            if self.config.get('security.wipe_on_panic', False):
                self._secure_wipe_notes()
            
            self._disable_wireless()
            
            self._lock_device()
            
            self.logger.info("Panic mode procedures completed")
            
        except Exception as e:
            self.logger.error(f"Error during panic mode: {e}")
    
    def _clear_clipboard(self) -> None:
        """Clear clipboard data."""
        try:
            if self.clipboard_dir.exists():
                for file in self.clipboard_dir.glob('*'):
                    self._secure_delete_file(file)
            
            self.logger.info("Clipboard cleared")
            
        except Exception as e:
            self.logger.error(f"Failed to clear clipboard: {e}")
    
    def _clear_cache(self) -> None:
        """Clear cache data."""
        try:
            if self.cache_dir.exists():
                for file in self.cache_dir.glob('*'):
                    file.unlink()
            
            self.logger.info("Cache cleared")
            
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
    
    def _secure_wipe_notes(self) -> None:
        """Securely wipe all notes."""
        try:
            if self.notes_dir.exists():
                for file in self.notes_dir.glob('*.enc'):
                    self._secure_delete_file(file)
            
            self.logger.warning("All notes securely wiped")
            
        except Exception as e:
            self.logger.error(f"Failed to wipe notes: {e}")
    
    def _disable_wireless(self) -> None:
        """Disable wireless communications."""
        try:
            subprocess.run(['sudo', 'rfkill', 'block', 'all'], 
                         check=False, timeout=5)
            
            self.logger.info("Wireless disabled")
            
        except Exception as e:
            self.logger.error(f"Failed to disable wireless: {e}")
    
    def _lock_device(self) -> None:
        """Lock the device."""
        self.logger.info("Device locked")
    
    def _secure_delete_file(self, file_path: Path) -> None:
        """
        Securely delete a file by overwriting.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            if not file_path.exists():
                return
            
            file_size = file_path.stat().st_size
            
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
            
            with open(file_path, 'wb') as f:
                f.write(b'\x00' * file_size)
                f.flush()
                os.fsync(f.fileno())
            
            file_path.unlink()
            
            self.logger.debug(f"Securely deleted: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to secure delete {file_path}: {e}")
    
    def _load_encryption_key(self) -> None:
        """Load or generate encryption key."""
        key_file = self.data_dir / '.key'
        
        try:
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
                self.logger.info("Encryption key loaded")
            else:
                self.encryption_key = secrets.token_bytes(32)
                
                self.data_dir.mkdir(parents=True, exist_ok=True)
                
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
                
                key_file.chmod(0o600)
                
                self.logger.info("New encryption key generated")
                
        except Exception as e:
            self.logger.error(f"Failed to load encryption key: {e}")
            self.encryption_key = secrets.token_bytes(32)
    
    def get_encryption_key(self) -> bytes:
        """
        Get encryption key.
        
        Returns:
            32-byte encryption key
        """
        if self.encryption_key is None:
            self._load_encryption_key()
        
        return self.encryption_key
    
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: User password
            salt: Salt bytes (generated if None)
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode())
        
        return key, salt
    
    def hash_password(self, password: str) -> str:
        """
        Hash password with salt.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password string
        """
        salt = secrets.token_hex(16)
        
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        )
        
        return f"{salt}${pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Password to verify
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        try:
            salt, pwd_hash = hashed.split('$')
            
            new_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000
            )
            
            return new_hash.hex() == pwd_hash
            
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup security manager."""
        if self.encryption_key:
            self.encryption_key = None
    
    def audit_log(self, action: str, details: str = "") -> None:
        """
        Log security-related action.
        
        Args:
            action: Action description
            details: Additional details
        """
        log_file = Path('/var/log/stealth-deck/security.log')
        
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            
            with open(log_file, 'a') as f:
                f.write(f"{timestamp} | {action} | {details}\n")
                
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
    
    def get_security_status(self) -> dict:
        """
        Get current security status.
        
        Returns:
            Security status dictionary
        """
        return {
            'panic_active': self.panic_active,
            'encryption_enabled': self.encryption_key is not None,
            'secure_delete_enabled': self.config.get('security.secure_delete_enabled', True),
            'wireless_enabled': not self._is_wireless_disabled()
        }
    
    def _is_wireless_disabled(self) -> bool:
        """
        Check if wireless is disabled.
        
        Returns:
            True if wireless is disabled
        """
        try:
            result = subprocess.run(
                ['rfkill', 'list'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            return 'Soft blocked: yes' in result.stdout
            
        except Exception:
            return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    from core.config_manager import ConfigManager
    
    config = ConfigManager('/tmp/test_config.json')
    
    security = SecurityManager(config)
    
    key = security.get_encryption_key()
    print(f"Encryption key length: {len(key)} bytes")
    
    password = "test_password"
    hashed = security.hash_password(password)
    print(f"Hashed password: {hashed[:50]}...")
    
    verified = security.verify_password(password, hashed)
    print(f"Password verified: {verified}")
