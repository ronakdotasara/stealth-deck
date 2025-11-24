"""
================================================================================
encryption.py - P2P Encryption Module
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Handles encryption and decryption for P2P transfers.
Uses AES-256-GCM for authenticated encryption.

Features:
- AES-256-GCM encryption
- Key exchange
- Nonce generation
- Authenticated encryption
- Session keys

================================================================================
"""

import logging
import secrets
import hashlib
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class P2PEncryption:
    """
    P2P encryption handler.
    
    Provides encryption and decryption for P2P transfers.
    """
    
    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize encryption.
        
        Args:
            master_key: Master encryption key (32 bytes)
        """
        self.logger = logging.getLogger('p2p_encryption')
        
        if master_key and len(master_key) == 32:
            self.master_key = master_key
        else:
            self.master_key = secrets.token_bytes(32)
        
        self.aesgcm = AESGCM(self.master_key)
        
        self.session_key: Optional[bytes] = None
        self.session_aesgcm: Optional[AESGCM] = None
    
    def generate_session_key(self) -> bytes:
        """
        Generate ephemeral session key.
        
        Returns:
            Session key (32 bytes)
        """
        self.session_key = secrets.token_bytes(32)
        self.session_aesgcm = AESGCM(self.session_key)
        
        self.logger.info("Session key generated")
        
        return self.session_key
    
    def set_session_key(self, session_key: bytes) -> bool:
        """
        Set session key from peer.
        
        Args:
            session_key: Session key (32 bytes)
            
        Returns:
            True if valid
        """
        if len(session_key) != 32:
            self.logger.error("Invalid session key length")
            return False
        
        self.session_key = session_key
        self.session_aesgcm = AESGCM(session_key)
        
        self.logger.info("Session key set")
        
        return True
    
    def encrypt(self, data: bytes, use_session_key: bool = True) -> bytes:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            use_session_key: Use session key if available
            
        Returns:
            Encrypted data (nonce + ciphertext)
        """
        try:
            if use_session_key and self.session_aesgcm:
                aesgcm = self.session_aesgcm
            else:
                aesgcm = self.aesgcm
            
            nonce = secrets.token_bytes(12)
            
            ciphertext = aesgcm.encrypt(nonce, data, None)
            
            return nonce + ciphertext
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: bytes, use_session_key: bool = True) -> bytes:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data (nonce + ciphertext)
            use_session_key: Use session key if available
            
        Returns:
            Decrypted data
        """
        try:
            if len(encrypted_data) < 12:
                raise ValueError("Invalid encrypted data")
            
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            
            if use_session_key and self.session_aesgcm:
                aesgcm = self.session_aesgcm
            else:
                aesgcm = self.aesgcm
            
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_chunk(self, chunk_data: bytes) -> bytes:
        """
        Encrypt transfer chunk.
        
        Args:
            chunk_data: Chunk data
            
        Returns:
            Encrypted chunk
        """
        return self.encrypt(chunk_data, use_session_key=True)
    
    def decrypt_chunk(self, encrypted_chunk: bytes) -> bytes:
        """
        Decrypt transfer chunk.
        
        Args:
            encrypted_chunk: Encrypted chunk
            
        Returns:
            Decrypted chunk
        """
        return self.decrypt(encrypted_chunk, use_session_key=True)
    
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive key from password.
        
        Args:
            password: Password string
            salt: Optional salt (16 bytes)
            
        Returns:
            Derived key (32 bytes)
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
        
        return key
    
    def compute_key_hash(self, key: bytes) -> str:
        """
        Compute key fingerprint.
        
        Args:
            key: Key bytes
            
        Returns:
            Hex fingerprint
        """
        sha256 = hashlib.sha256(key)
        return sha256.hexdigest()[:16]
    
    def verify_key_hash(self, key: bytes, expected_hash: str) -> bool:
        """
        Verify key fingerprint.
        
        Args:
            key: Key bytes
            expected_hash: Expected fingerprint
            
        Returns:
            True if valid
        """
        actual_hash = self.compute_key_hash(key)
        return actual_hash == expected_hash
    
    def exchange_keys(self, peer_public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Perform key exchange (simplified).
        
        Args:
            peer_public_key: Peer's public key
            
        Returns:
            Tuple of (our_public_key, shared_secret)
        """
        our_private_key = secrets.token_bytes(32)
        our_public_key = hashlib.sha256(our_private_key).digest()
        
        shared_secret = hashlib.sha256(
            our_private_key + peer_public_key
        ).digest()
        
        return (our_public_key, shared_secret)
    
    def clear_session_key(self) -> None:
        """Clear session key."""
        self.session_key = None
        self.session_aesgcm = None
        
        self.logger.info("Session key cleared")
    
    def rotate_master_key(self, new_key: bytes) -> bool:
        """
        Rotate master key.
        
        Args:
            new_key: New master key (32 bytes)
            
        Returns:
            True if successful
        """
        if len(new_key) != 32:
            return False
        
        self.master_key = new_key
        self.aesgcm = AESGCM(new_key)
        
        self.logger.info("Master key rotated")
        
        return True
    
    def get_encryption_info(self) -> dict:
        """
        Get encryption information.
        
        Returns:
            Info dictionary
        """
        return {
            'algorithm': 'AES-256-GCM',
            'key_size': 256,
            'nonce_size': 96,
            'has_session_key': self.session_key is not None,
            'master_key_hash': self.compute_key_hash(self.master_key)
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    encryption = P2PEncryption()
    
    test_data = b"Hello, this is a test message!"
    
    encrypted = encryption.encrypt(test_data)
    print(f"Encrypted: {len(encrypted)} bytes")
    
    decrypted = encryption.decrypt(encrypted)
    print(f"Decrypted: {decrypted.decode()}")
    
    assert test_data == decrypted
    print("Encryption test passed!")
