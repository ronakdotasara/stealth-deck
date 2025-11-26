#!/usr/bin/env python3
"""
================================================================================
key_generator.py - Encryption Key Generator
================================================================================
Version: 1.0.0
Date: 2025-11-25

Generates encryption keys for Stealth Deck.
================================================================================
"""

import os
import sys
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class KeyGenerator:
    """
    Encryption key generator.
    
    Generates secure keys for various purposes.
    """
    
    @staticmethod
    def generate_master_key() -> bytes:
        """
        Generate master encryption key.
        
        Returns:
            32-byte key
        """
        return secrets.token_bytes(32)
    
    @staticmethod
    def generate_session_key() -> bytes:
        """
        Generate session key.
        
        Returns:
            32-byte key
        """
        return secrets.token_bytes(32)
    
    @staticmethod
    def generate_fernet_key() -> bytes:
        """
        Generate Fernet key.
        
        Returns:
            Fernet key
        """
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes = None) -> tuple:
        """
        Derive key from password.
        
        Args:
            password: Password string
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
            iterations=100000
        )
        
        key = kdf.derive(password.encode())
        
        return key, salt
    
    @staticmethod
    def hash_unlock_code(code: str) -> str:
        """
        Hash unlock code.
        
        Args:
            code: Unlock code
            
        Returns:
            Hash string
        """
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def generate_device_id() -> str:
        """
        Generate unique device ID.
        
        Returns:
            Device ID string
        """
        return secrets.token_hex(16)


def main():
    """Main function."""
    print("Stealth Deck - Encryption Key Generator")
    print("=" * 60)
    
    generator = KeyGenerator()
    
    print("\n1. Master Key:")
    master_key = generator.generate_master_key()
    print(f"   {master_key.hex()}")
    
    print("\n2. Fernet Key:")
    fernet_key = generator.generate_fernet_key()
    print(f"   {fernet_key.decode()}")
    
    print("\n3. Session Key:")
    session_key = generator.generate_session_key()
    print(f"   {session_key.hex()}")
    
    print("\n4. Password-Derived Key:")
    password = "SecurePassword123"
    key, salt = generator.derive_key_from_password(password)
    print(f"   Key:  {key.hex()}")
    print(f"   Salt: {salt.hex()}")
    
    print("\n5. Unlock Code Hash:")
    unlock_code = "555"
    code_hash = generator.hash_unlock_code(unlock_code)
    print(f"   Code: {unlock_code}")
    print(f"   Hash: {code_hash}")
    
    print("\n6. Device ID:")
    device_id = generator.generate_device_id()
    print(f"   {device_id}")
    
    print("\n" + "=" * 60)
    
    # Save to file option
    save = input("\nSave keys to file? (y/n): ").lower()
    
    if save == 'y':
        filename = f"keys_{secrets.token_hex(4)}.txt"
        
        with open(filename, 'w') as f:
            f.write("Stealth Deck Encryption Keys\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Master Key: {master_key.hex()}\n")
            f.write(f"Fernet Key: {fernet_key.decode()}\n")
            f.write(f"Session Key: {session_key.hex()}\n")
            f.write(f"Device ID: {device_id}\n")
            f.write(f"Unlock Code Hash: {code_hash}\n")
        
        print(f"\n✓ Keys saved to: {filename}")
        print("⚠️  Keep this file secure!")


if __name__ == '__main__':
    main()
