"""
================================================================================
crypto_utils.py - Cryptographic Utilities
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Cryptographic utility functions for hashing, key derivation, and random generation.

Features:
- Password hashing
- Key derivation
- Secure random generation
- Hash functions
- Salt generation

================================================================================
"""

import logging
import secrets
import hashlib
import base64
from typing import Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class CryptoUtils:
    """
    Cryptographic utility functions.
    
    Provides common crypto operations.
    """
    
    @staticmethod
    def generate_key(length: int = 32) -> bytes:
        """
        Generate random cryptographic key.
        
        Args:
            length: Key length in bytes
            
        Returns:
            Random key
        """
        return secrets.token_bytes(length)
    
    @staticmethod
    def generate_salt(length: int = 16) -> bytes:
        """
        Generate random salt.
        
        Args:
            length: Salt length in bytes
            
        Returns:
            Random salt
        """
        return secrets.token_bytes(length)
    
    @staticmethod
    def generate_token_hex(length: int = 32) -> str:
        """
        Generate random hex token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            Hex string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_token_urlsafe(length: int = 32) -> str:
        """
        Generate URL-safe random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            URL-safe string
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None,
                     iterations: int = 100000) -> tuple:
        """
        Hash password using PBKDF2.
        
        Args:
            password: Password to hash
            salt: Optional salt (generated if None)
            iterations: Number of iterations
            
        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = CryptoUtils.generate_salt()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode())
        
        return (key, salt)
    
    @staticmethod
    def verify_password(password: str, hash_value: bytes, salt: bytes,
                       iterations: int = 100000) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Password to verify
            hash_value: Stored hash
            salt: Salt used for hashing
            iterations: Number of iterations
            
        Returns:
            True if password matches
        """
        try:
            derived, _ = CryptoUtils.hash_password(password, salt, iterations)
            return secrets.compare_digest(derived, hash_value)
        except Exception:
            return False
    
    @staticmethod
    def derive_key(password: str, salt: bytes, length: int = 32,
                  iterations: int = 100000) -> bytes:
        """
        Derive key from password.
        
        Args:
            password: Password
            salt: Salt
            length: Key length
            iterations: Number of iterations
            
        Returns:
            Derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=length,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        return kdf.derive(password.encode())
    
    @staticmethod
    def sha256(data: bytes) -> bytes:
        """
        Compute SHA-256 hash.
        
        Args:
            data: Data to hash
            
        Returns:
            Hash digest
        """
        return hashlib.sha256(data).digest()
    
    @staticmethod
    def sha256_hex(data: bytes) -> str:
        """
        Compute SHA-256 hash (hex).
        
        Args:
            data: Data to hash
            
        Returns:
            Hash hex string
        """
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def sha512(data: bytes) -> bytes:
        """
        Compute SHA-512 hash.
        
        Args:
            data: Data to hash
            
        Returns:
            Hash digest
        """
        return hashlib.sha512(data).digest()
    
    @staticmethod
    def md5(data: bytes) -> str:
        """
        Compute MD5 hash (for non-security uses).
        
        Args:
            data: Data to hash
            
        Returns:
            Hash hex string
        """
        return hashlib.md5(data).hexdigest()
    
    @staticmethod
    def base64_encode(data: bytes) -> str:
        """
        Encode data to base64.
        
        Args:
            data: Data to encode
            
        Returns:
            Base64 string
        """
        return base64.b64encode(data).decode('utf-8')
    
    @staticmethod
    def base64_decode(data: str) -> bytes:
        """
        Decode base64 data.
        
        Args:
            data: Base64 string
            
        Returns:
            Decoded bytes
        """
        return base64.b64decode(data)
    
    @staticmethod
    def constant_time_compare(a: bytes, b: bytes) -> bool:
        """
        Constant-time comparison.
        
        Args:
            a: First value
            b: Second value
            
        Returns:
            True if equal
        """
        return secrets.compare_digest(a, b)
    
    @staticmethod
    def generate_uuid() -> str:
        """
        Generate UUID v4.
        
        Returns:
            UUID string
        """
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def secure_delete_data(data: bytearray) -> None:
        """
        Securely delete data from memory.
        
        Args:
            data: Data to delete
        """
        if isinstance(data, bytearray):
            for i in range(len(data)):
                data[i] = 0
    
    @staticmethod
    def xor_bytes(a: bytes, b: bytes) -> bytes:
        """
        XOR two byte strings.
        
        Args:
            a: First bytes
            b: Second bytes
            
        Returns:
            XORed result
        """
        return bytes(x ^ y for x, y in zip(a, b))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test key generation
    key = CryptoUtils.generate_key()
    print(f"Generated key: {len(key)} bytes")
    
    # Test password hashing
    password = "test_password"
    hash_val, salt = CryptoUtils.hash_password(password)
    print(f"Password hash: {len(hash_val)} bytes")
    
    # Test verification
    valid = CryptoUtils.verify_password(password, hash_val, salt)
    print(f"Password valid: {valid}")
    
    # Test SHA-256
    data = b"Hello, World!"
    hash_hex = CryptoUtils.sha256_hex(data)
    print(f"SHA-256: {hash_hex}")
