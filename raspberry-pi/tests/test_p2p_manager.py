"""
================================================================================
test_p2p_manager.py - P2P Manager Tests
================================================================================
Version: 1.0.0
Date: 2025-11-25

Unit tests for P2P transfer manager.
================================================================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.p2p.transfer_handler import TransferHandler, TransferState


class TestTransferHandler:
    """Test suite for transfer handler."""
    
    @pytest.fixture
    def transfer_handler(self):
        """Create transfer handler."""
        return TransferHandler(chunk_size=1024)
    
    def test_initialization(self, transfer_handler):
        """Test handler initialization."""
        assert transfer_handler.chunk_size == 1024
        assert transfer_handler.transfer_state == TransferState.IDLE
    
    def test_prepare_send(self, transfer_handler, tmp_path):
        """Test preparing file for send."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content" * 100)
        
        metadata = transfer_handler.prepare_send(str(test_file))
        
        assert metadata is not None
        assert metadata.file_name == "test.txt"
        assert metadata.file_size > 0
    
    def test_prepare_send_nonexistent(self, transfer_handler):
        """Test preparing nonexistent file."""
        metadata = transfer_handler.prepare_send("/nonexistent/file.txt")
        
        assert metadata is None
    
    def test_send_chunk(self, transfer_handler, tmp_path):
        """Test sending chunk."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content" * 100)
        
        transfer_handler.prepare_send(str(test_file))
        
        chunk_data = transfer_handler.send_chunk(0)
        
        assert chunk_data is not None
        assert len(chunk_data) <= 1024
    
    def test_prepare_receive(self, transfer_handler, tmp_path):
        """Test preparing to receive."""
        from src.p2p.transfer_handler import TransferMetadata, TransferType
        
        metadata = TransferMetadata(
            transfer_id="test123",
            transfer_type=TransferType.FILE,
            file_name="received.txt",
            file_size=1024,
            chunks_total=1,
            chunk_size=1024,
            checksum="abc123",
            created_at=1234567890.0
        )
        
        result = transfer_handler.prepare_receive(metadata)
        
        assert result is True
    
    def test_receive_chunk(self, transfer_handler, tmp_path):
        """Test receiving chunk."""
        from src.p2p.transfer_handler import TransferMetadata, TransferType
        
        metadata = TransferMetadata(
            transfer_id="test123",
            transfer_type=TransferType.FILE,
            file_name="received.txt",
            file_size=100,
            chunks_total=1,
            chunk_size=1024,
            checksum="abc123",
            created_at=1234567890.0
        )
        
        transfer_handler.prepare_receive(metadata)
        
        result = transfer_handler.receive_chunk(0, b"Test data")
        
        assert result is True
    
    def test_pause_transfer(self, transfer_handler, tmp_path):
        """Test pausing transfer."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        transfer_handler.prepare_send(str(test_file))
        transfer_handler.transfer_state = TransferState.SENDING
        
        result = transfer_handler.pause_transfer()
        
        assert result is True
        assert transfer_handler.transfer_state == TransferState.PAUSED
    
    def test_resume_transfer(self, transfer_handler):
        """Test resuming transfer."""
        transfer_handler.transfer_state = TransferState.PAUSED
        transfer_handler.current_transfer = {'chunks_sent': 0}
        
        result = transfer_handler.resume_transfer()
        
        assert result is True
    
    def test_cancel_transfer(self, transfer_handler, tmp_path):
        """Test canceling transfer."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        transfer_handler.prepare_send(str(test_file))
        
        transfer_handler.cancel_transfer()
        
        assert transfer_handler.transfer_state == TransferState.CANCELLED
    
    def test_get_progress(self, transfer_handler, tmp_path):
        """Test getting progress."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content" * 100)
        
        transfer_handler.prepare_send(str(test_file))
        
        progress = transfer_handler.get_progress()
        
        assert 'state' in progress
        assert 'progress' in progress
        assert progress['progress'] >= 0


class TestTransferEncryption:
    """Test transfer encryption."""
    
    @pytest.fixture
    def transfer_handler(self):
        """Create transfer handler."""
        return TransferHandler()
    
    def test_chunk_encryption(self, transfer_handler):
        """Test chunk encryption/decryption."""
        from src.p2p.encryption import P2PEncryption
        
        encryption = P2PEncryption()
        encryption.generate_session_key()
        
        original_data = b"Test chunk data"
        
        encrypted = encryption.encrypt_chunk(original_data)
        decrypted = encryption.decrypt_chunk(encrypted)
        
        assert decrypted == original_data


class TestTransferStatistics:
    """Test transfer statistics."""
    
    @pytest.fixture
    def transfer_handler(self):
        """Create transfer handler."""
        return TransferHandler()
    
    def test_get_statistics(self, transfer_handler):
        """Test getting statistics."""
        stats = transfer_handler.get_statistics()
        
        assert 'total_transfers' in stats
        assert 'successful_transfers' in stats
        assert 'failed_transfers' in stats
        assert 'bytes_transferred' in stats
    
    def test_statistics_update(self, transfer_handler, tmp_path):
        """Test statistics update after transfer."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        transfer_handler.prepare_send(str(test_file))
        
        # Simulate successful transfer
        transfer_handler._complete_send()
        
        stats = transfer_handler.get_statistics()
        
        assert stats['total_transfers'] > 0
        assert stats['successful_transfers'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
