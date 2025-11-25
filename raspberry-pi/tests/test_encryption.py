"""
================================================================================
test_encryption.py - Unit Tests for Encryption Modules
================================================================================
Version: 1.0.0
Date: 2025-11-25

Test coverage for encryption functionality.
================================================================================
"""

import pytest
from unittest.mock import Mock
from src.core.security_manager import SecurityManager
from src.p2p.encryption import P2PEncryption


class TestSecurityManager:
    """Test suite for security manager."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            'security.encryption_enabled': True,
            'security.wipe_on_panic': False,
            'security.key_iterations': 100000
        }.get(key, default)
        return config
    
    @pytest.fixture
    def security_manager(self, mock_config):
        """Create security manager."""
        return SecurityManager(mock_config)
    
    def test_initialization(self, security_manager):
        """Test manager initialization."""
        assert security_manager.encryption_enabled is True
        assert security_manager.master_key is not None
    
    def test_get_encryption_key(self, security_manager):
        """Test encryption key retrieval."""
        key = security_manager.get_encryption_key()
        
        assert key is not None
        assert len(key) == 32
    
    def test_hash_password(self, security_manager):
        """Test password hashing."""
        password = "test_password"
        
        hashed = security_manager.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 32
    
    def test_verify_password(self, security_manager):
        """Test password verification."""
        password = "test_password"
        hashed = security_manager.hash_password(password)
        
        # Correct password
        assert security_manager.verify_password(password, hashed) is True
        
        # Wrong password
        assert security_manager.verify_password("wrong", hashed) is False
    
    def test_derive_key(self, security_manager):
        """Test key derivation."""
        password = "test_password"
        salt = b"test_salt_16byte"
        
        key1 = security_manager.derive_key(password, salt)
        key2 = security_manager.derive_key(password, salt)
        
        assert key1 == key2
        assert len(key1) == 32
    
    def test_encrypt_decrypt(self, security_manager):
        """Test encryption and decryption."""
        plaintext = b"Secret message"
        
        encrypted = security_manager.encrypt_data(plaintext)
        decrypted = security_manager.decrypt_data(encrypted)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
    
    def test_encrypt_empty_data(self, security_manager):
        """Test encrypting empty data."""
        encrypted = security_manager.encrypt_data(b"")
        
        assert encrypted is not None
        assert len(encrypted) > 0
    
    def test_decrypt_invalid_data(self, security_manager):
        """Test decrypting invalid data."""
        with pytest.raises(Exception):
            security_manager.decrypt_data(b"invalid")
    
    def test_secure_wipe(self, security_manager, tmp_path):
        """Test secure file wiping."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Sensitive data")
        
        result = security_manager.secure_wipe(str(test_file))
        
        assert result is True
        assert not test_file.exists()
    
    def test_panic_mode(self, security_manager):
        """Test panic mode activation."""
        security_manager.panic_mode()
        
        # Check that panic state is set
        # (implementation dependent)


class TestP2PEncryption:
    """Test suite for P2P encryption."""
    
    @pytest.fixture
    def encryption(self):
        """Create P2P encryption instance."""
        return P2PEncryption()
    
    def test_initialization(self, encryption):
        """Test encryption initialization."""
        assert encryption.master_key is not None
        assert len(encryption.master_key) == 32
    
    def test_generate_session_key(self, encryption):
        """Test session key generation."""
        session_key = encryption.generate_session_key()
        
        assert session_key is not None
        assert len(session_key) == 32
        assert encryption.session_key == session_key
    
    def test_set_session_key(self, encryption):
        """Test setting session key."""
        test_key = b'\x00' * 32
        
        result = encryption.set_session_key(test_key)
        
        assert result is True
        assert encryption.session_key == test_key
    
    def test_set_invalid_session_key(self, encryption):
        """Test setting invalid session key."""
        result = encryption.set_session_key(b"short")
        
        assert result is False
    
    def test_encrypt_decrypt_master_key(self, encryption):
        """Test encryption with master key."""
        plaintext = b"Test message"
        
        encrypted = encryption.encrypt(plaintext, use_session_key=False)
        decrypted = encryption.decrypt(encrypted, use_session_key=False)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_session_key(self, encryption):
        """Test encryption with session key."""
        encryption.generate_session_key()
        
        plaintext = b"Test message"
        
        encrypted = encryption.encrypt(plaintext, use_session_key=True)
        decrypted = encryption.decrypt(encrypted, use_session_key=True)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
    
    def test_encrypt_chunk(self, encryption):
        """Test chunk encryption."""
        encryption.generate_session_key()
        
        chunk_data = b"File chunk data"
        
        encrypted = encryption.encrypt_chunk(chunk_data)
        decrypted = encryption.decrypt_chunk(encrypted)
        
        assert decrypted == chunk_data
    
    def test_different_nonces(self, encryption):
        """Test that different encryptions use different nonces."""
        plaintext = b"Same message"
        
        encrypted1 = encryption.encrypt(plaintext)
        encrypted2 = encryption.encrypt(plaintext)
        
        # Encrypted data should be different due to different nonces
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same plaintext
        assert encryption.decrypt(encrypted1) == plaintext
        assert encryption.decrypt(encrypted2) == plaintext
    
    def test_compute_key_hash(self, encryption):
        """Test key hash computation."""
        key = b'\x00' * 32
        
        hash1 = encryption.compute_key_hash(key)
        hash2 = encryption.compute_key_hash(key)
        
        assert hash1 == hash2
        assert len(hash1) == 16
    
    def test_verify_key_hash(self, encryption):
        """Test key hash verification."""
        key = b'\x00' * 32
        correct_hash = encryption.compute_key_hash(key)
        wrong_hash = "0" * 16
        
        assert encryption.verify_key_hash(key, correct_hash) is True
        assert encryption.verify_key_hash(key, wrong_hash) is False
    
    def test_derive_key_from_password(self, encryption):
        """Test key derivation from password."""
        password = "test_password"
        salt = b"fixed_salt_12345"
        
        key1 = encryption.derive_key_from_password(password, salt)
        key2 = encryption.derive_key_from_password(password, salt)
        
        assert key1 == key2
        assert len(key1) == 32
    
    def test_clear_session_key(self, encryption):
        """Test clearing session key."""
        encryption.generate_session_key()
        
        assert encryption.session_key is not None
        
        encryption.clear_session_key()
        
        assert encryption.session_key is None
    
    def test_rotate_master_key(self, encryption):
        """Test master key rotation."""
        old_key = encryption.master_key
        new_key = b'\xFF' * 32
        
        result = encryption.rotate_master_key(new_key)
        
        assert result is True
        assert encryption.master_key != old_key
        assert encryption.master_key == new_key
    
    def test_get_encryption_info(self, encryption):
        """Test encryption info retrieval."""
        encryption.generate_session_key()
        
        info = encryption.get_encryption_info()
        
        assert info['algorithm'] == 'AES-256-GCM'
        assert info['key_size'] == 256
        assert info['has_session_key'] is True


class TestEncryptionEdgeCases:
    """Test edge cases for encryption."""
    
    @pytest.fixture
    def encryption(self):
        """Create encryption instance."""
        return P2PEncryption()
    
    def test_encrypt_large_data(self, encryption):
        """Test encrypting large data."""
        large_data = b"X" * (1024 * 1024)  # 1MB
        
        encrypted = encryption.encrypt(large_data)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == large_data
    
    def test_encrypt_binary_data(self, encryption):
        """Test encrypting binary data."""
        import os
        binary_data = os.urandom(1000)
        
        encrypted = encryption.encrypt(binary_data)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == binary_data
    
    def test_encrypt_unicode(self, encryption):
        """Test encrypting unicode text."""
        unicode_text = "Hello 世界 🌍".encode('utf-8')
        
        encrypted = encryption.encrypt(unicode_text)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == unicode_text
    
    def test_decrypt_truncated_data(self, encryption):
        """Test decrypting truncated data."""
        plaintext = b"Test message"
        encrypted = encryption.encrypt(plaintext)
        
        # Truncate encrypted data
        truncated = encrypted[:10]
        
        with pytest.raises(Exception):
            encryption.decrypt(truncated)
    
    def test_decrypt_modified_data(self, encryption):
        """Test decrypting modified data."""
        plaintext = b"Test message"
        encrypted = encryption.encrypt(plaintext)
        
        # Modify encrypted data
        modified = bytearray(encrypted)
        modified[-1] ^= 0xFF
        
        with pytest.raises(Exception):
            encryption.decrypt(bytes(modified))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
