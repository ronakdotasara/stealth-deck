"""
================================================================================
file_utils.py - File Operation Utilities
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
File operation utilities for safe file handling, atomic writes, and secure deletion.

Features:
- Atomic file writes
- Secure file deletion
- Safe file operations
- Directory management
- File integrity checks

================================================================================
"""

import logging
import os
import shutil
import tempfile
import hashlib
from typing import Optional, List
from pathlib import Path


class FileUtils:
    """
    File operation utilities.
    
    Provides safe and secure file operations.
    """
    
    @staticmethod
    def atomic_write(file_path: str, content: bytes, mode: str = 'wb') -> bool:
        """
        Atomically write file.
        
        Args:
            file_path: Target file path
            content: Content to write
            mode: Write mode
            
        Returns:
            True if successful
        """
        try:
            file_path = Path(file_path)
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            fd, temp_path = tempfile.mkstemp(
                dir=str(file_path.parent),
                prefix='.tmp_'
            )
            
            try:
                with os.fdopen(fd, mode) as f:
                    f.write(content)
                
                os.replace(temp_path, str(file_path))
                
                return True
                
            except Exception as e:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e
                
        except Exception as e:
            logging.error(f"Atomic write failed: {e}")
            return False
    
    @staticmethod
    def secure_delete(file_path: str, passes: int = 3) -> bool:
        """
        Securely delete file.
        
        Args:
            file_path: File to delete
            passes: Number of overwrite passes
            
        Returns:
            True if successful
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return True
            
            file_size = file_path.stat().st_size
            
            with open(file_path, 'r+b') as f:
                for i in range(passes):
                    f.seek(0)
                    
                    if i == 0:
                        pattern = b'\xFF' * file_size
                    elif i == 1:
                        pattern = b'\x00' * file_size
                    else:
                        pattern = os.urandom(file_size)
                    
                    f.write(pattern)
                    f.flush()
                    os.fsync(f.fileno())
            
            file_path.unlink()
            
            return True
            
        except Exception as e:
            logging.error(f"Secure delete failed: {e}")
            return False
    
    @staticmethod
    def safe_read(file_path: str, binary: bool = False) -> Optional[bytes]:
        """
        Safely read file.
        
        Args:
            file_path: File to read
            binary: Read as binary
            
        Returns:
            File content or None
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            mode = 'rb' if binary else 'r'
            
            with open(file_path, mode) as f:
                content = f.read()
            
            return content if binary else content.encode()
            
        except Exception as e:
            logging.error(f"File read failed: {e}")
            return None
    
    @staticmethod
    def safe_write(file_path: str, content: bytes, append: bool = False) -> bool:
        """
        Safely write file.
        
        Args:
            file_path: Target file
            content: Content to write
            append: Append mode
            
        Returns:
            True if successful
        """
        try:
            file_path = Path(file_path)
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'ab' if append else 'wb'
            
            with open(file_path, mode) as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            logging.error(f"File write failed: {e}")
            return False
    
    @staticmethod
    def calculate_checksum(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
        """
        Calculate file checksum.
        
        Args:
            file_path: File to checksum
            algorithm: Hash algorithm
            
        Returns:
            Checksum hex string or None
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            if algorithm == 'sha256':
                hasher = hashlib.sha256()
            elif algorithm == 'md5':
                hasher = hashlib.md5()
            elif algorithm == 'sha512':
                hasher = hashlib.sha512()
            else:
                return None
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            logging.error(f"Checksum calculation failed: {e}")
            return None
    
    @staticmethod
    def verify_checksum(file_path: str, expected: str, algorithm: str = 'sha256') -> bool:
        """
        Verify file checksum.
        
        Args:
            file_path: File to verify
            expected: Expected checksum
            algorithm: Hash algorithm
            
        Returns:
            True if valid
        """
        actual = FileUtils.calculate_checksum(file_path, algorithm)
        
        if actual is None:
            return False
        
        return actual.lower() == expected.lower()
    
    @staticmethod
    def copy_file(src: str, dst: str, secure: bool = False) -> bool:
        """
        Copy file.
        
        Args:
            src: Source file
            dst: Destination file
            secure: Delete source after copy
            
        Returns:
            True if successful
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            if not src_path.exists():
                return False
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_path, dst_path)
            
            if secure:
                FileUtils.secure_delete(src)
            
            return True
            
        except Exception as e:
            logging.error(f"File copy failed: {e}")
            return False
    
    @staticmethod
    def move_file(src: str, dst: str) -> bool:
        """
        Move file atomically.
        
        Args:
            src: Source file
            dst: Destination file
            
        Returns:
            True if successful
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            if not src_path.exists():
                return False
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            return True
            
        except Exception as e:
            logging.error(f"File move failed: {e}")
            return False
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """
        Ensure directory exists.
        
        Args:
            directory: Directory path
            
        Returns:
            True if exists/created
        """
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"Directory creation failed: {e}")
            return False
    
    @staticmethod
    def list_files(directory: str, pattern: str = '*', recursive: bool = False) -> List[str]:
        """
        List files in directory.
        
        Args:
            directory: Directory path
            pattern: File pattern
            recursive: Recursive search
            
        Returns:
            List of file paths
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return []
            
            if recursive:
                files = dir_path.rglob(pattern)
            else:
                files = dir_path.glob(pattern)
            
            return [str(f) for f in files if f.is_file()]
            
        except Exception as e:
            logging.error(f"File listing failed: {e}")
            return []
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get file size.
        
        Args:
            file_path: File path
            
        Returns:
            Size in bytes, or -1 if error
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return -1
    
    @staticmethod
    def get_free_space(path: str = '/') -> int:
        """
        Get free disk space.
        
        Args:
            path: Path to check
            
        Returns:
            Free space in bytes
        """
        try:
            stat = shutil.disk_usage(path)
            return stat.free
        except Exception:
            return 0
    
    @staticmethod
    def cleanup_old_files(directory: str, max_age_days: int) -> int:
        """
        Delete old files.
        
        Args:
            directory: Directory to clean
            max_age_days: Maximum age in days
            
        Returns:
            Number of files deleted
        """
        import time
        
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return 0
            
            count = 0
            cutoff_time = time.time() - (max_age_days * 86400)
            
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        count += 1
            
            return count
            
        except Exception as e:
            logging.error(f"Cleanup failed: {e}")
            return 0
    
    @staticmethod
    def compress_file(file_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Compress file with gzip.
        
        Args:
            file_path: File to compress
            output_path: Output path (optional)
            
        Returns:
            Compressed file path or None
        """
        import gzip
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            if output_path is None:
                output_path = str(file_path) + '.gz'
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Compression failed: {e}")
            return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test atomic write
    test_file = '/tmp/test_atomic.txt'
    FileUtils.atomic_write(test_file, b'Test content')
    print(f"Atomic write: {Path(test_file).exists()}")
    
    # Test checksum
    checksum = FileUtils.calculate_checksum(test_file)
    print(f"Checksum: {checksum}")
    
    # Test secure delete
    FileUtils.secure_delete(test_file)
    print(f"Deleted: {not Path(test_file).exists()}")
