"""
================================================================================
transfer_handler.py - P2P Transfer Handler
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Handles P2P file transfer operations with chunking and resume support.
Manages transfer state, progress tracking, and error recovery.

Features:
- Chunked transfers
- Resume capability
- Progress tracking
- Error recovery
- Multiple file types
- Transfer queue

================================================================================
"""

import logging
import os
import hashlib
import time
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class TransferState(Enum):
    """Transfer state enumeration."""
    IDLE = 'idle'
    PREPARING = 'preparing'
    SENDING = 'sending'
    RECEIVING = 'receiving'
    PAUSED = 'paused'
    COMPLETE = 'complete'
    ERROR = 'error'
    CANCELLED = 'cancelled'


class TransferType(Enum):
    """Transfer type enumeration."""
    FILE = 'file'
    TEXT = 'text'
    IMAGE = 'image'
    CAMERA = 'camera'


@dataclass
class TransferMetadata:
    """Transfer metadata."""
    transfer_id: str
    transfer_type: TransferType
    file_name: str
    file_size: int
    chunks_total: int
    chunk_size: int
    checksum: str
    created_at: float


class TransferHandler:
    """
    P2P transfer handler.
    
    Manages file transfers with chunking and progress tracking.
    """
    
    def __init__(self, chunk_size: int = 1024):
        """
        Initialize transfer handler.
        
        Args:
            chunk_size: Size of each chunk in bytes
        """
        self.logger = logging.getLogger('transfer_handler')
        
        self.chunk_size = chunk_size
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        self.current_transfer: Optional[Dict[str, Any]] = None
        self.transfer_state = TransferState.IDLE
        
        self.transfer_dir = Path('/tmp/stealth-deck/transfers')
        self.transfer_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress_callback: Optional[Callable] = None
        self.complete_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
        self.statistics = {
            'total_transfers': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'bytes_transferred': 0
        }
    
    def prepare_send(self, file_path: str, transfer_type: TransferType = TransferType.FILE,
                    metadata: Optional[Dict] = None) -> Optional[TransferMetadata]:
        """
        Prepare file for sending.
        
        Args:
            file_path: Path to file
            transfer_type: Type of transfer
            metadata: Optional metadata
            
        Returns:
            Transfer metadata or None
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return None
            
            file_size = file_path.stat().st_size
            
            if file_size > self.max_file_size:
                self.logger.error(f"File too large: {file_size} bytes")
                return None
            
            chunks_total = (file_size + self.chunk_size - 1) // self.chunk_size
            
            checksum = self._calculate_checksum(file_path)
            
            transfer_id = hashlib.md5(f"{file_path}{time.time()}".encode()).hexdigest()
            
            transfer_metadata = TransferMetadata(
                transfer_id=transfer_id,
                transfer_type=transfer_type,
                file_name=file_path.name,
                file_size=file_size,
                chunks_total=chunks_total,
                chunk_size=self.chunk_size,
                checksum=checksum,
                created_at=time.time()
            )
            
            self.current_transfer = {
                'metadata': transfer_metadata,
                'file_path': str(file_path),
                'chunks_sent': 0,
                'bytes_sent': 0,
                'start_time': time.time(),
                'user_metadata': metadata or {}
            }
            
            self.transfer_state = TransferState.PREPARING
            
            self.logger.info(f"Prepared transfer: {file_path.name} ({file_size} bytes)")
            
            return transfer_metadata
            
        except Exception as e:
            self.logger.error(f"Transfer preparation failed: {e}")
            return None
    
    def send_chunk(self, chunk_index: int) -> Optional[bytes]:
        """
        Get chunk data for sending.
        
        Args:
            chunk_index: Index of chunk to send
            
        Returns:
            Chunk data or None
        """
        try:
            if not self.current_transfer:
                return None
            
            file_path = Path(self.current_transfer['file_path'])
            metadata = self.current_transfer['metadata']
            
            if chunk_index >= metadata.chunks_total:
                self.logger.error(f"Invalid chunk index: {chunk_index}")
                return None
            
            offset = chunk_index * self.chunk_size
            
            with open(file_path, 'rb') as f:
                f.seek(offset)
                chunk_data = f.read(self.chunk_size)
            
            self.current_transfer['chunks_sent'] = chunk_index + 1
            self.current_transfer['bytes_sent'] += len(chunk_data)
            
            self.transfer_state = TransferState.SENDING
            
            if self.progress_callback:
                progress = (chunk_index + 1) / metadata.chunks_total * 100
                self.progress_callback(progress)
            
            if chunk_index + 1 >= metadata.chunks_total:
                self._complete_send()
            
            return chunk_data
            
        except Exception as e:
            self.logger.error(f"Chunk send failed: {e}")
            self._error_occurred(str(e))
            return None
    
    def prepare_receive(self, metadata: TransferMetadata) -> bool:
        """
        Prepare to receive file.
        
        Args:
            metadata: Transfer metadata
            
        Returns:
            True if prepared
        """
        try:
            output_path = self.transfer_dir / metadata.file_name
            
            self.current_transfer = {
                'metadata': metadata,
                'output_path': str(output_path),
                'chunks_received': 0,
                'bytes_received': 0,
                'start_time': time.time(),
                'file_handle': None
            }
            
            self.current_transfer['file_handle'] = open(output_path, 'wb')
            
            self.transfer_state = TransferState.RECEIVING
            
            self.logger.info(f"Prepared to receive: {metadata.file_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Receive preparation failed: {e}")
            return False
    
    def receive_chunk(self, chunk_index: int, chunk_data: bytes) -> bool:
        """
        Receive and write chunk data.
        
        Args:
            chunk_index: Index of received chunk
            chunk_data: Chunk data
            
        Returns:
            True if successful
        """
        try:
            if not self.current_transfer:
                return False
            
            metadata = self.current_transfer['metadata']
            file_handle = self.current_transfer['file_handle']
            
            if chunk_index >= metadata.chunks_total:
                self.logger.error(f"Invalid chunk index: {chunk_index}")
                return False
            
            expected_offset = chunk_index * self.chunk_size
            file_handle.seek(expected_offset)
            file_handle.write(chunk_data)
            
            self.current_transfer['chunks_received'] = chunk_index + 1
            self.current_transfer['bytes_received'] += len(chunk_data)
            
            if self.progress_callback:
                progress = (chunk_index + 1) / metadata.chunks_total * 100
                self.progress_callback(progress)
            
            if chunk_index + 1 >= metadata.chunks_total:
                self._complete_receive()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Chunk receive failed: {e}")
            self._error_occurred(str(e))
            return False
    
    def pause_transfer(self) -> bool:
        """
        Pause current transfer.
        
        Returns:
            True if paused
        """
        if self.transfer_state in [TransferState.SENDING, TransferState.RECEIVING]:
            self.transfer_state = TransferState.PAUSED
            self.logger.info("Transfer paused")
            return True
        return False
    
    def resume_transfer(self) -> bool:
        """
        Resume paused transfer.
        
        Returns:
            True if resumed
        """
        if self.transfer_state == TransferState.PAUSED:
            if self.current_transfer:
                if 'chunks_sent' in self.current_transfer:
                    self.transfer_state = TransferState.SENDING
                else:
                    self.transfer_state = TransferState.RECEIVING
                self.logger.info("Transfer resumed")
                return True
        return False
    
    def cancel_transfer(self) -> None:
        """Cancel current transfer."""
        if self.current_transfer:
            if 'file_handle' in self.current_transfer and self.current_transfer['file_handle']:
                self.current_transfer['file_handle'].close()
            
            self.transfer_state = TransferState.CANCELLED
            
            self.statistics['failed_transfers'] += 1
            
            self.current_transfer = None
            
            self.logger.info("Transfer cancelled")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get transfer progress.
        
        Returns:
            Progress dictionary
        """
        if not self.current_transfer:
            return {
                'state': self.transfer_state.value,
                'progress': 0
            }
        
        metadata = self.current_transfer['metadata']
        
        if 'chunks_sent' in self.current_transfer:
            chunks_done = self.current_transfer['chunks_sent']
            bytes_done = self.current_transfer['bytes_sent']
        else:
            chunks_done = self.current_transfer['chunks_received']
            bytes_done = self.current_transfer['bytes_received']
        
        progress = (chunks_done / metadata.chunks_total * 100) if metadata.chunks_total > 0 else 0
        
        elapsed = time.time() - self.current_transfer['start_time']
        speed = bytes_done / elapsed if elapsed > 0 else 0
        
        remaining_bytes = metadata.file_size - bytes_done
        eta = remaining_bytes / speed if speed > 0 else 0
        
        return {
            'state': self.transfer_state.value,
            'progress': progress,
            'file_name': metadata.file_name,
            'file_size': metadata.file_size,
            'chunks_done': chunks_done,
            'chunks_total': metadata.chunks_total,
            'bytes_done': bytes_done,
            'speed': speed,
            'eta': eta
        }
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate file checksum.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 checksum
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _verify_checksum(self, file_path: Path, expected: str) -> bool:
        """
        Verify file checksum.
        
        Args:
            file_path: Path to file
            expected: Expected checksum
            
        Returns:
            True if valid
        """
        actual = self._calculate_checksum(file_path)
        return actual == expected
    
    def _complete_send(self) -> None:
        """Complete send transfer."""
        self.transfer_state = TransferState.COMPLETE
        
        self.statistics['total_transfers'] += 1
        self.statistics['successful_transfers'] += 1
        self.statistics['bytes_transferred'] += self.current_transfer['bytes_sent']
        
        if self.complete_callback:
            self.complete_callback(self.current_transfer)
        
        self.logger.info("Send transfer complete")
        
        self.current_transfer = None
    
    def _complete_receive(self) -> None:
        """Complete receive transfer."""
        if self.current_transfer['file_handle']:
            self.current_transfer['file_handle'].close()
        
        output_path = Path(self.current_transfer['output_path'])
        metadata = self.current_transfer['metadata']
        
        if self._verify_checksum(output_path, metadata.checksum):
            self.transfer_state = TransferState.COMPLETE
            
            self.statistics['total_transfers'] += 1
            self.statistics['successful_transfers'] += 1
            self.statistics['bytes_transferred'] += self.current_transfer['bytes_received']
            
            if self.complete_callback:
                self.complete_callback(self.current_transfer)
            
            self.logger.info("Receive transfer complete")
        else:
            self.logger.error("Checksum verification failed")
            output_path.unlink()
            self._error_occurred("Checksum mismatch")
        
        self.current_transfer = None
    
    def _error_occurred(self, error: str) -> None:
        """Handle transfer error."""
        self.transfer_state = TransferState.ERROR
        
        if self.current_transfer and 'file_handle' in self.current_transfer:
            if self.current_transfer['file_handle']:
                self.current_transfer['file_handle'].close()
        
        self.statistics['failed_transfers'] += 1
        
        if self.error_callback:
            self.error_callback(error)
        
        self.logger.error(f"Transfer error: {error}")
        
        self.current_transfer = None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get transfer statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.statistics.copy()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    handler = TransferHandler()
    
    print("Transfer handler initialized")
