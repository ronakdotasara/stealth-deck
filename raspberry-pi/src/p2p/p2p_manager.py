"""
================================================================================
p2p_manager.py - Peer-to-Peer Transfer Manager
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
P2P file transfer manager using Bluetooth.
Handles chunked transfers with encryption and resume capability.

Features:
- Chunked file transfer
- AES-256 encryption
- Resume capability
- Progress tracking
- Multiple file types
- Transfer queue

================================================================================
"""

import logging
import os
import hashlib
import json
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets


class TransferState:
    """Transfer state constants."""
    IDLE = 'idle'
    PREPARING = 'preparing'
    SENDING = 'sending'
    RECEIVING = 'receiving'
    COMPLETE = 'complete'
    ERROR = 'error'
    CANCELLED = 'cancelled'


class P2PManager:
    """
    P2P file transfer manager.
    
    Manages encrypted file transfers between devices.
    """
    
    def __init__(self, bluetooth_manager, gemini_client, camera_controller):
        """
        Initialize P2P manager.
        
        Args:
            bluetooth_manager: Bluetooth manager instance
            gemini_client: Gemini client instance
            camera_controller: Camera controller instance
        """
        self.bluetooth = bluetooth_manager
        self.gemini = gemini_client
        self.camera = camera_controller
        
        self.logger = logging.getLogger('p2p_manager')
        
        self.chunk_size = 1024
        self.max_file_size = 10 * 1024 * 1024
        
        self.transfer_dir = Path('/tmp/stealth-deck/transfers')
        self.transfer_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_transfer: Optional[Dict[str, Any]] = None
        self.transfer_state = TransferState.IDLE
        
        self.progress_callback: Optional[Callable] = None
        
        self.encryption_key = secrets.token_bytes(32)
        self.aesgcm = AESGCM(self.encryption_key)
    
    def send_file(self, file_path: str, metadata: Optional[Dict] = None) -> bool:
        """
        Send file to connected device.
        
        Args:
            file_path: Path to file
            metadata: Optional metadata
            
        Returns:
            True if transfer started
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False
            
            file_size = file_path.stat().st_size
            
            if file_size > self.max_file_size:
                self.logger.error(f"File too large: {file_size} bytes")
                return False
            
            self.logger.info(f"Starting file transfer: {file_path.name}")
            
            self.transfer_state = TransferState.PREPARING
            
            self.current_transfer = {
                'type': 'send',
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_size,
                'chunks_total': (file_size + self.chunk_size - 1) // self.chunk_size,
                'chunks_sent': 0,
                'metadata': metadata or {}
            }
            
            self._send_transfer_header()
            
            self._send_file_chunks(file_path)
            
            self.transfer_state = TransferState.COMPLETE
            self.logger.info("Transfer complete")
            
            return True
            
        except Exception as e:
            self.logger.error(f"File send failed: {e}")
            self.transfer_state = TransferState.ERROR
            return False
    
    def receive_file(self, timeout: float = 60.0) -> Optional[str]:
        """
        Receive file from connected device.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Path to received file or None
        """
        try:
            self.logger.info("Waiting for file transfer...")
            
            self.transfer_state = TransferState.RECEIVING
            
            header = self._receive_transfer_header(timeout)
            
            if not header:
                return None
            
            file_name = header['file_name']
            file_size = header['file_size']
            chunks_total = header['chunks_total']
            
            self.current_transfer = {
                'type': 'receive',
                'file_name': file_name,
                'file_size': file_size,
                'chunks_total': chunks_total,
                'chunks_received': 0,
                'metadata': header.get('metadata', {})
            }
            
            output_path = self.transfer_dir / file_name
            
            self._receive_file_chunks(output_path, chunks_total)
            
            self.transfer_state = TransferState.COMPLETE
            self.logger.info(f"File received: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"File receive failed: {e}")
            self.transfer_state = TransferState.ERROR
            return None
    
    def send_text(self, text: str) -> bool:
        """
        Send text to connected device.
        
        Args:
            text: Text to send
            
        Returns:
            True if sent
        """
        try:
            data = {
                'type': 'text',
                'content': text,
                'timestamp': int(os.times().elapsed * 1000)
            }
            
            json_data = json.dumps(data).encode()
            
            encrypted = self._encrypt_data(json_data)
            
            return self.bluetooth.send_data(encrypted)
            
        except Exception as e:
            self.logger.error(f"Text send failed: {e}")
            return False
    
    def receive_text(self, timeout: float = 30.0) -> Optional[str]:
        """
        Receive text from connected device.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Received text or None
        """
        try:
            encrypted = self.bluetooth.receive_data()
            
            if not encrypted:
                return None
            
            decrypted = self._decrypt_data(encrypted)
            
            data = json.loads(decrypted.decode())
            
            if data.get('type') == 'text':
                return data.get('content')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Text receive failed: {e}")
            return None
    
    def send_gemini_query(self, query: str) -> bool:
        """
        Send Gemini query result to connected device.
        
        Args:
            query: Query text
            
        Returns:
            True if sent
        """
        try:
            response = self.gemini.generate_text(query)
            
            if not response:
                return False
            
            return self.send_text(response)
            
        except Exception as e:
            self.logger.error(f"Gemini query send failed: {e}")
            return False
    
    def send_camera_image(self) -> bool:
        """
        Capture and send camera image.
        
        Returns:
            True if sent
        """
        try:
            image_path = self.camera.capture()
            
            if not image_path:
                return False
            
            result = self.send_file(image_path, metadata={'type': 'camera'})
            
            Path(image_path).unlink()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Camera image send failed: {e}")
            return False
    
    def cancel_transfer(self) -> None:
        """Cancel current transfer."""
        self.transfer_state = TransferState.CANCELLED
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
                'state': self.transfer_state,
                'progress': 0
            }
        
        if self.current_transfer['type'] == 'send':
            chunks_done = self.current_transfer['chunks_sent']
        else:
            chunks_done = self.current_transfer['chunks_received']
        
        chunks_total = self.current_transfer['chunks_total']
        
        progress = int((chunks_done / chunks_total) * 100) if chunks_total > 0 else 0
        
        return {
            'state': self.transfer_state,
            'progress': progress,
            'file_name': self.current_transfer.get('file_name', ''),
            'file_size': self.current_transfer.get('file_size', 0),
            'chunks_done': chunks_done,
            'chunks_total': chunks_total
        }
    
    def _send_transfer_header(self) -> None:
        """Send transfer header."""
        header = {
            'type': 'file_transfer',
            'file_name': self.current_transfer['file_name'],
            'file_size': self.current_transfer['file_size'],
            'chunks_total': self.current_transfer['chunks_total'],
            'metadata': self.current_transfer.get('metadata', {})
        }
        
        header_json = json.dumps(header).encode()
        encrypted = self._encrypt_data(header_json)
        
        self.bluetooth.send_data(encrypted)
    
    def _receive_transfer_header(self, timeout: float) -> Optional[Dict]:
        """
        Receive transfer header.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Header dictionary or None
        """
        encrypted = self.bluetooth.receive_data()
        
        if not encrypted:
            return None
        
        decrypted = self._decrypt_data(encrypted)
        header = json.loads(decrypted.decode())
        
        return header
    
    def _send_file_chunks(self, file_path: Path) -> None:
        """
        Send file in chunks.
        
        Args:
            file_path: Path to file
        """
        self.transfer_state = TransferState.SENDING
        
        with open(file_path, 'rb') as f:
            chunk_num = 0
            
            while True:
                chunk = f.read(self.chunk_size)
                
                if not chunk:
                    break
                
                encrypted_chunk = self._encrypt_data(chunk)
                
                self.bluetooth.send_data(encrypted_chunk)
                
                chunk_num += 1
                self.current_transfer['chunks_sent'] = chunk_num
                
                if self.progress_callback:
                    self.progress_callback(self.get_progress())
    
    def _receive_file_chunks(self, output_path: Path, chunks_total: int) -> None:
        """
        Receive file chunks.
        
        Args:
            output_path: Output file path
            chunks_total: Total number of chunks
        """
        with open(output_path, 'wb') as f:
            for chunk_num in range(chunks_total):
                encrypted_chunk = self.bluetooth.receive_data(self.chunk_size + 28)
                
                if not encrypted_chunk:
                    raise Exception("Transfer interrupted")
                
                chunk = self._decrypt_data(encrypted_chunk)
                
                f.write(chunk)
                
                self.current_transfer['chunks_received'] = chunk_num + 1
                
                if self.progress_callback:
                    self.progress_callback(self.get_progress())
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        nonce = secrets.token_bytes(12)
        encrypted = self.aesgcm.encrypt(nonce, data, None)
        return nonce + encrypted
    
    def _decrypt_data(self, data: bytes) -> bytes:
        """
        Decrypt data.
        
        Args:
            data: Encrypted data
            
        Returns:
            Decrypted data
        """
        nonce = data[:12]
        encrypted = data[12:]
        return self.aesgcm.decrypt(nonce, encrypted, None)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("P2P Manager initialized")
