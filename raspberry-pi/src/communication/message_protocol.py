"""
================================================================================
message_protocol.py - MessagePack Protocol Handler
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
MessagePack serialization for efficient data transfer.
Alternative to JSON for binary data and smaller payloads.

Features:
- Compact binary format
- Type preservation
- Fast serialization
- Smaller than JSON

================================================================================
"""

import logging
import msgpack
from typing import Any, Optional


class MessageProtocol:
    """
    MessagePack protocol handler.
    
    Provides efficient serialization/deserialization.
    """
    
    def __init__(self):
        """Initialize message protocol."""
        self.logger = logging.getLogger('message_protocol')
        
        self.packer = msgpack.Packer(use_bin_type=True)
        self.unpacker = msgpack.Unpacker(raw=False)
    
    def pack(self, data: Any) -> Optional[bytes]:
        """
        Pack data to MessagePack format.
        
        Args:
            data: Data to pack
            
        Returns:
            Packed bytes or None
        """
        try:
            packed = self.packer.pack(data)
            return packed
            
        except Exception as e:
            self.logger.error(f"Packing failed: {e}")
            return None
    
    def unpack(self, data: bytes) -> Optional[Any]:
        """
        Unpack MessagePack data.
        
        Args:
            data: Packed bytes
            
        Returns:
            Unpacked data or None
        """
        try:
            unpacked = msgpack.unpackb(data, raw=False)
            return unpacked
            
        except Exception as e:
            self.logger.error(f"Unpacking failed: {e}")
            return None
    
    def pack_dict(self, dictionary: dict) -> Optional[bytes]:
        """
        Pack dictionary.
        
        Args:
            dictionary: Dict to pack
            
        Returns:
            Packed bytes or None
        """
        return self.pack(dictionary)
    
    def unpack_dict(self, data: bytes) -> Optional[dict]:
        """
        Unpack to dictionary.
        
        Args:
            data: Packed bytes
            
        Returns:
            Dictionary or None
        """
        result = self.unpack(data)
        
        if isinstance(result, dict):
            return result
        
        return None
    
    def pack_list(self, items: list) -> Optional[bytes]:
        """
        Pack list.
        
        Args:
            items: List to pack
            
        Returns:
            Packed bytes or None
        """
        return self.pack(items)
    
    def unpack_list(self, data: bytes) -> Optional[list]:
        """
        Unpack to list.
        
        Args:
            data: Packed bytes
            
        Returns:
            List or None
        """
        result = self.unpack(data)
        
        if isinstance(result, list):
            return result
        
        return None
    
    def get_packed_size(self, data: Any) -> int:
        """
        Get size of packed data.
        
        Args:
            data: Data to measure
            
        Returns:
            Size in bytes
        """
        try:
            packed = self.pack(data)
            
            if packed:
                return len(packed)
            
            return 0
            
        except Exception:
            return 0
    
    def compare_with_json(self, data: Any) -> dict:
        """
        Compare MessagePack vs JSON size.
        
        Args:
            data: Data to compare
            
        Returns:
            Comparison dictionary
        """
        import json
        
        try:
            msgpack_size = self.get_packed_size(data)
            
            json_bytes = json.dumps(data).encode('utf-8')
            json_size = len(json_bytes)
            
            savings = json_size - msgpack_size
            savings_percent = (savings / json_size * 100) if json_size > 0 else 0
            
            return {
                'msgpack_size': msgpack_size,
                'json_size': json_size,
                'savings_bytes': savings,
                'savings_percent': round(savings_percent, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
            return {}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    protocol = MessageProtocol()
    
    # Test data
    test_data = {
        'name': 'Stealth Deck',
        'version': '0.5.0',
        'features': ['AI', 'Camera', 'Security'],
        'count': 42
    }
    
    # Pack
    packed = protocol.pack(test_data)
    print(f"Packed: {len(packed)} bytes")
    
    # Unpack
    unpacked = protocol.unpack(packed)
    print(f"Unpacked: {unpacked}")
    
    # Compare
    comparison = protocol.compare_with_json(test_data)
    print(f"Comparison: {comparison}")
