"""
================================================================================
packet_analyzer.py - UART Packet Analyzer
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Analyzes UART protocol packets for debugging.
Provides detailed packet analysis and protocol validation.

Features:
- Packet validation
- CRC verification
- Protocol compliance checking
- Timing analysis
- Error detection

================================================================================
"""

import struct
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class PacketError(Enum):
    """Packet error types."""
    NONE = "No error"
    INVALID_START = "Invalid start marker"
    INVALID_TYPE = "Invalid message type"
    LENGTH_MISMATCH = "Payload length mismatch"
    CRC_MISMATCH = "CRC verification failed"
    TIMEOUT = "Reception timeout"


@dataclass
class PacketInfo:
    """Packet information."""
    timestamp: float
    msg_type: int
    msg_type_name: str
    length: int
    payload: bytes
    crc: int
    crc_valid: bool
    error: PacketError
    latency: Optional[float] = None


class PacketAnalyzer:
    """
    UART packet analyzer.
    
    Analyzes protocol packets for correctness.
    """
    
    def __init__(self):
        """Initialize packet analyzer."""
        self.packets: List[PacketInfo] = []
        self.statistics = {
            'total': 0,
            'valid': 0,
            'errors': 0,
            'crc_errors': 0
        }
        
        self.msg_types = {
            0x00: "NONE",
            0x01: "DISPLAY_TEXT",
            0x02: "DISPLAY_CLEAR",
            0x03: "KEYPRESS",
            0x04: "MODE_CHANGE",
            0x05: "CAMERA_CAPTURE",
            0x06: "CAMERA_RESULT",
            0x10: "HEARTBEAT",
            0x11: "STATUS",
            0x12: "ERROR",
            0x20: "P2P_START",
            0x21: "P2P_DATA",
            0x22: "P2P_END",
            0xFE: "PANIC",
            0xFF: "DEBUG"
        }
    
    def analyze_packet(self, raw_data: bytes) -> PacketInfo:
        """
        Analyze raw packet data.
        
        Args:
            raw_data: Raw packet bytes
            
        Returns:
            Packet information
        """
        timestamp = time.time()
        error = PacketError.NONE
        
        # Check minimum length
        if len(raw_data) < 8:
            error = PacketError.INVALID_START
        
        # Parse header
        try:
            start = raw_data[0]
            
            if start != 0xAA:
                error = PacketError.INVALID_START
            
            msg_type = raw_data[1]
            length = struct.unpack('>H', raw_data[2:4])[0]
            
            # Extract payload
            payload = raw_data[4:4+length]
            
            # Extract CRC
            crc = struct.unpack('>H', raw_data[4+length:6+length])[0]
            
            # Verify CRC
            calculated_crc = self.calculate_crc(raw_data[1:4+length])
            crc_valid = (crc == calculated_crc)
            
            if not crc_valid:
                error = PacketError.CRC_MISMATCH
                self.statistics['crc_errors'] += 1
            
            # Verify message type
            if msg_type not in self.msg_types:
                error = PacketError.INVALID_TYPE
            
            # Create packet info
            packet = PacketInfo(
                timestamp=timestamp,
                msg_type=msg_type,
                msg_type_name=self.msg_types.get(msg_type, "UNKNOWN"),
                length=length,
                payload=payload,
                crc=crc,
                crc_valid=crc_valid,
                error=error
            )
            
            self.packets.append(packet)
            self.statistics['total'] += 1
            
            if error == PacketError.NONE:
                self.statistics['valid'] += 1
            else:
                self.statistics['errors'] += 1
            
            return packet
        
        except Exception as e:
            # Parse error
            packet = PacketInfo(
                timestamp=timestamp,
                msg_type=0,
                msg_type_name="PARSE_ERROR",
                length=0,
                payload=b'',
                crc=0,
                crc_valid=False,
                error=PacketError.INVALID_START
            )
            
            self.statistics['errors'] += 1
            
            return packet
    
    def calculate_crc(self, data: bytes) -> int:
        """
        Calculate CRC16-CCITT.
        
        Args:
            data: Data bytes
            
        Returns:
            CRC value
        """
        crc = 0xFFFF
        
        for byte in data:
            crc ^= byte << 8
            
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                
                crc &= 0xFFFF
        
        return crc
    
    def verify_protocol_compliance(self, packet: PacketInfo) -> List[str]:
        """
        Verify protocol compliance.
        
        Args:
            packet: Packet to verify
            
        Returns:
            List of compliance issues
        """
        issues = []
        
        # Check message type validity
        if packet.msg_type not in self.msg_types:
            issues.append(f"Invalid message type: 0x{packet.msg_type:02X}")
        
        # Check payload length
        if packet.length > 1024:
            issues.append(f"Payload too large: {packet.length} bytes")
        
        # Check CRC
        if not packet.crc_valid:
            issues.append("CRC verification failed")
        
        return issues
    
    def analyze_timing(self, window_seconds: float = 1.0) -> Dict:
        """
        Analyze timing of recent packets.
        
        Args:
            window_seconds: Time window to analyze
            
        Returns:
            Timing statistics
        """
        current_time = time.time()
        cutoff = current_time - window_seconds
        
        recent_packets = [
            p for p in self.packets
            if p.timestamp >= cutoff
        ]
        
        if len(recent_packets) < 2:
            return {
                'count': len(recent_packets),
                'rate': 0,
                'avg_interval': 0
            }
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(recent_packets)):
            interval = recent_packets[i].timestamp - recent_packets[i-1].timestamp
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals)
        rate = len(recent_packets) / window_seconds
        
        return {
            'count': len(recent_packets),
            'rate': rate,
            'avg_interval': avg_interval,
            'min_interval': min(intervals),
            'max_interval': max(intervals)
        }
    
    def get_statistics(self) -> Dict:
        """
        Get analysis statistics.
        
        Returns:
            Statistics dictionary
        """
        error_rate = 0
        if self.statistics['total'] > 0:
            error_rate = self.statistics['errors'] / self.statistics['total'] * 100
        
        # Count message types
        type_counts = {}
        for packet in self.packets:
            type_name = packet.msg_type_name
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            'total_packets': self.statistics['total'],
            'valid_packets': self.statistics['valid'],
            'error_packets': self.statistics['errors'],
            'crc_errors': self.statistics['crc_errors'],
            'error_rate': round(error_rate, 2),
            'message_types': type_counts
        }
    
    def generate_report(self) -> str:
        """
        Generate analysis report.
        
        Returns:
            Report text
        """
        stats = self.get_statistics()
        timing = self.analyze_timing(10.0)
        
        report = f"""
UART Packet Analysis Report
============================

Overall Statistics:
  Total Packets:   {stats['total_packets']}
  Valid Packets:   {stats['valid_packets']}
  Error Packets:   {stats['error_packets']}
  CRC Errors:      {stats['crc_errors']}
  Error Rate:      {stats['error_rate']}%

Timing (last 10 seconds):
  Packet Count:    {timing['count']}
  Packet Rate:     {timing['rate']:.2f} packets/sec
  Avg Interval:    {timing['avg_interval']*1000:.2f} ms

Message Types:
"""
        
        for msg_type, count in sorted(stats['message_types'].items()):
            percentage = (count / stats['total_packets'] * 100) if stats['total_packets'] > 0 else 0
            report += f"  {msg_type:20s}: {count:5d} ({percentage:5.1f}%)\n"
        
        return report
    
    def export_packets(self, filename: str):
        """
        Export packets to file.
        
        Args:
            filename: Output filename
        """
        with open(filename, 'w') as f:
            f.write("Timestamp,Type,Type_Name,Length,Payload_Hex,CRC,CRC_Valid,Error\n")
            
            for packet in self.packets:
                f.write(f"{packet.timestamp:.6f},")
                f.write(f"0x{packet.msg_type:02X},")
                f.write(f"{packet.msg_type_name},")
                f.write(f"{packet.length},")
                f.write(f"{packet.payload.hex()},")
                f.write(f"0x{packet.crc:04X},")
                f.write(f"{packet.crc_valid},")
                f.write(f"{packet.error.value}\n")


if __name__ == '__main__':
    analyzer = PacketAnalyzer()
    
    # Test packet
    test_packet = bytes([
        0xAA,  # Start
        0x01,  # Type: DISPLAY_TEXT
        0x00, 0x05,  # Length: 5
        0x48, 0x65, 0x6C, 0x6C, 0x6F,  # Payload: "Hello"
        0x00, 0x00  # CRC (placeholder)
    ])
    
    # Calculate correct CRC
    crc = analyzer.calculate_crc(test_packet[1:9])
    test_packet = test_packet[:9] + struct.pack('>H', crc)
    
    # Analyze
    packet_info = analyzer.analyze_packet(test_packet)
    
    print(f"Packet Type: {packet_info.msg_type_name}")
    print(f"CRC Valid: {packet_info.crc_valid}")
    print(f"Error: {packet_info.error.value}")
    
    # Generate report
    print("\n" + analyzer.generate_report())
