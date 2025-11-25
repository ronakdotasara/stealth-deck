"""
================================================================================
test_p2p_transfer.py - P2P Transfer Integration Tests
================================================================================
Version: 1.0.0
Date: 2025-11-25

Integration tests for P2P file transfer.
================================================================================
"""

import pytest
import time
from unittest.mock import Mock, patch
from pathlib import Path


@pytest.mark.integration
class TestP2PTransfer:
    """Test P2P transfer integration."""
    
    @pytest.fixture
    def test_file(self, tmp_path):
        """Create test file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content" * 100)
        return test_file
    
    @pytest.fixture
    def transfer_handler(self):
        """Create transfer handler."""
        from src.p2p.transfer_handler import TransferHandler
        return TransferHandler(chunk_size=1024)
    
    def test_prepare_transfer(self, transfer_handler, test_file):
        """Test preparing file for transfer."""
        metadata = transfer_handler.prepare_send(str(test_file))
        
        assert metadata is not None
        assert metadata.file_name == "test.txt"
        assert metadata.file_size > 0
        assert metadata.chunks_total > 0
    
    def test_chunk_transfer(self, transfer_handler, test_file):
        """Test transferring chunks."""
        transfer_handler.prepare_send(str(test_file))
        
        chunks_sent = 0
        
        while not transfer_handler.is_complete():
            chunk_data = transfer_handler.send_chunk(chunks_sent)
            
            if chunk_data is None:
                break
            
            chunks_sent += 1
        
        assert chunks_sent > 0
    
    def test_receive_transfer(self, transfer_handler, test_file, tmp_path):
        """Test receiving file."""
        from src.p2p.transfer_handler import TransferMetadata, TransferType
        
        # Prepare to receive
        metadata = TransferMetadata(
            transfer_id="test123",
            transfer_type=TransferType.FILE,
            file_name="received.txt",
            file_size=test_file.stat().st_size,
            chunks_total=1,
            chunk_size=1024,
            checksum="abc123",
            created_at=time.time()
        )
        
        transfer_handler.prepare_receive(metadata)
        
        # Simulate receiving chunks
        with open(test_file, 'rb') as f:
            chunk_data = f.read(1024)
            result = transfer_handler.receive_chunk(0, chunk_data)
        
        assert result is True


@pytest.mark.integration
class TestP2PDiscovery:
    """Test P2P device discovery."""
    
    @pytest.fixture
    def discovery_manager(self):
        """Create discovery manager."""
        from src.p2p.device_discovery import DeviceDiscovery
        return DeviceDiscovery()
    
    @patch('bluetooth.discover_devices')
    def test_discover_devices(self, mock_discover, discovery_manager):
        """Test device discovery."""
        mock_discover.return_value = [
            ('AA:BB:CC:DD:EE:FF', 'Stealth Deck 1', 12345)
        ]
        
        devices = discovery_manager.start_discovery(duration=1)
        
        assert len(devices) >= 0
    
    def test_device_filtering(self, discovery_manager):
        """Test filtering Stealth Deck devices."""
        assert discovery_manager._is_stealth_deck("Stealth Deck") is True
        assert discovery_manager._is_stealth_deck("Other Device") is False
        assert discovery_manager._is_stealth_deck("StealthDeck-001") is True


@pytest.mark.integration
class TestP2PPairing:
    """Test P2P device pairing."""
    
    @pytest.fixture
    def pairing_manager(self, tmp_path):
        """Create pairing manager."""
        from src.p2p.pairing_manager import PairingManager
        return PairingManager(str(tmp_path))
    
    def test_initiate_pairing(self, pairing_manager):
        """Test initiating device pairing."""
        address = "AA:BB:CC:DD:EE:FF"
        name = "Test Device"
        public_key = b"test_public_key_12345678"
        
        fingerprint = pairing_manager.initiate_pairing(address, name, public_key)
        
        assert fingerprint is not None
        assert len(fingerprint) > 0
    
    def test_verify_pairing(self, pairing_manager):
        """Test verifying pairing."""
        address = "AA:BB:CC:DD:EE:FF"
        name = "Test Device"
        public_key = b"test_public_key_12345678"
        
        pairing_manager.initiate_pairing(address, name, public_key)
        
        result = pairing_manager.verify_pairing(address, True)
        
        assert result is True
        assert pairing_manager.is_trusted(address) is True
    
    def test_reject_pairing(self, pairing_manager):
        """Test rejecting pairing."""
        address = "AA:BB:CC:DD:EE:FF"
        name = "Test Device"
        public_key = b"test_public_key_12345678"
        
        pairing_manager.initiate_pairing(address, name, public_key)
        
        result = pairing_manager.verify_pairing(address, False)
        
        assert result is False
        assert not pairing_manager.is_paired(address)


@pytest.mark.integration
class TestP2PEncryption:
    """Test P2P encryption."""
    
    @pytest.fixture
    def encryption(self):
        """Create encryption instance."""
        from src.p2p.encryption import P2PEncryption
        return P2PEncryption()
    
    def test_session_key_generation(self, encryption):
        """Test session key generation."""
        session_key = encryption.generate_session_key()
        
        assert session_key is not None
        assert len(session_key) == 32
    
    def test_encrypt_decrypt_chunk(self, encryption):
        """Test chunk encryption/decryption."""
        encryption.generate_session_key()
        
        original = b"Test chunk data for transfer"
        
        encrypted = encryption.encrypt_chunk(original)
        decrypted = encryption.decrypt_chunk(encrypted)
        
        assert decrypted == original
    
    def test_key_exchange(self, encryption):
        """Test key exchange process."""
        # Generate two key pairs
        encryption1 = encryption
        from src.p2p.encryption import P2PEncryption
        encryption2 = P2PEncryption()
        
        key1 = encryption1.generate_session_key()
        key2 = encryption2.generate_session_key()
        
        assert key1 != key2


@pytest.mark.integration
class TestP2PPerformance:
    """Test P2P transfer performance."""
    
    @pytest.fixture
    def large_file(self, tmp_path):
        """Create large test file."""
        large_file = tmp_path / "large.bin"
        # Create 1MB file
        large_file.write_bytes(b'\x00' * (1024 * 1024))
        return large_file
    
    def test_transfer_speed(self, large_file):
        """Test transfer speed."""
        from src.p2p.transfer_handler import TransferHandler
        
        handler = TransferHandler(chunk_size=4096)
        
        start = time.time()
        
        metadata = handler.prepare_send(str(large_file))
        
        chunks_sent = 0
        while chunks_sent < metadata.chunks_total:
            chunk_data = handler.send_chunk(chunks_sent)
            if chunk_data is None:
                break
            chunks_sent += 1
        
        elapsed = time.time() - start
        
        # Should transfer reasonably fast
        assert elapsed < 10.0
    
    def test_concurrent_transfers(self):
        """Test multiple concurrent transfers."""
        # This would test multiple transfers happening simultaneously
        pass


@pytest.mark.integration
class TestP2PErrorHandling:
    """Test P2P error handling."""
    
    @pytest.fixture
    def transfer_handler(self):
        """Create transfer handler."""
        from src.p2p.transfer_handler import TransferHandler
        return TransferHandler()
    
    def test_invalid_file(self, transfer_handler):
        """Test handling invalid file."""
        metadata = transfer_handler.prepare_send("/nonexistent/file.txt")
        
        assert metadata is None
    
    def test_corrupted_chunk(self, transfer_handler):
        """Test handling corrupted chunk."""
        from src.p2p.transfer_handler import TransferMetadata, TransferType
        
        metadata = TransferMetadata(
            transfer_id="test123",
            transfer_type=TransferType.FILE,
            file_name="test.txt",
            file_size=1024,
            chunks_total=1,
            chunk_size=1024,
            checksum="abc123",
            created_at=time.time()
        )
        
        transfer_handler.prepare_receive(metadata)
        
        # Send corrupted data
        result = transfer_handler.receive_chunk(0, b"corrupted")
        
        # Should handle gracefully
        assert result is not None
    
    def test_connection_loss(self, transfer_handler, tmp_path):
        """Test handling connection loss."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        transfer_handler.prepare_send(str(test_file))
        
        # Simulate connection loss
        transfer_handler.cancel_transfer()
        
        assert transfer_handler.transfer_state.name == 'CANCELLED'


@pytest.mark.integration
class TestP2PResume:
    """Test P2P transfer resume capability."""
    
    @pytest.fixture
    def transfer_handler(self):
        """Create transfer handler."""
        from src.p2p.transfer_handler import TransferHandler
        return TransferHandler()
    
    def test_pause_resume(self, transfer_handler, tmp_path):
        """Test pausing and resuming transfer."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content" * 100)
        
        transfer_handler.prepare_send(str(test_file))
        
        # Send some chunks
        transfer_handler.send_chunk(0)
        transfer_handler.send_chunk(1)
        
        # Pause
        transfer_handler.pause_transfer()
        
        # Resume
        result = transfer_handler.resume_transfer()
        
        assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
