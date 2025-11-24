"""
================================================================================
uart_handler.py - UART Communication Handler for Raspberry Pi
================================================================================
Version: 1.0.1
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
UART communication handler for Raspberry Pi side of the Stealth Deck.
Provides bidirectional communication with ESP32 using the custom binary
protocol with CRC16 checksums and automatic retry.

================================================================================
"""

import serial
import time
import struct
import threading
import logging
from typing import Optional, Dict, List, Any, Callable
from queue import Queue, Empty
from dataclasses import dataclass
from enum import IntEnum

# ============================================================================
# CONSTANTS
# ============================================================================

START_BYTE = 0xAA
MAX_PAYLOAD_SIZE = 1024
MAX_FRAME_SIZE = MAX_PAYLOAD_SIZE + 7

TIMEOUT_MS = 500
RETRY_COUNT = 3
READ_TIMEOUT = 0.1
HEARTBEAT_INTERVAL = 5.0
CONNECTION_TIMEOUT = 10.0

# ============================================================================
# MESSAGE TYPES
# ============================================================================

class MessageType(IntEnum):
    """UART message types"""
    DISPLAY_TEXT = 0x01
    DISPLAY_IMAGE = 0x02
    KEYPRESS = 0x03
    CAMERA_CAPTURE = 0x04
    MODE_CHANGE = 0x05
    PANIC = 0x06
    HEARTBEAT = 0x07
    BATTERY_STATUS = 0x08
    P2P_DATA = 0x09
    ACK = 0x0A
    NACK = 0x0B

# ============================================================================
# PARSER STATES
# ============================================================================

class ParserState(IntEnum):
    """Parser state machine states"""
    IDLE = 0
    TYPE = 1
    LENGTH_H = 2
    LENGTH_L = 3
    PAYLOAD = 4
    CRC_H = 5
    CRC_L = 6

# ============================================================================
# CRC16-CCITT LOOKUP TABLE
# ============================================================================

CRC16_CCITT_TABLE = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
    0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
    0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
    0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
    0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
    0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
    0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
    0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
    0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
    0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
    0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
    0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
    0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
    0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
    0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
    0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
    0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
    0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
    0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
    0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
    0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
    0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
    0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
]

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class UARTMessage:
    """UART message structure"""
    type: int
    payload: bytes
    sequence: int = 0
    timestamp: float = 0.0
    needs_ack: bool = False
    retry_count: int = 0

@dataclass
class UARTStats:
    """UART communication statistics"""
    messages_sent: int = 0
    messages_received: int = 0
    bytes_transferred: int = 0
    crc_errors: int = 0
    timeouts: int = 0
    retries: int = 0
    acks_sent: int = 0
    acks_received: int = 0
    nacks_sent: int = 0
    nacks_received: int = 0

# ============================================================================
# UART HANDLER CLASS
# ============================================================================

class UARTHandler:
    """
    UART communication handler for Raspberry Pi.
    
    Handles bidirectional communication with ESP32 using custom binary
    protocol with CRC16 checksums and automatic retry.
    """
    
    def __init__(self, port: str = '/dev/serial0', baudrate: int = 115200):
        """
        Initialize UART handler.
        
        Args:
            port: Serial port device (default: /dev/serial0)
            baudrate: Baud rate (default: 115200)
        """
        self.port = port
        self.baudrate = baudrate
        
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        
        self.parser_state = ParserState.IDLE
        self.current_type = 0
        self.current_length = 0
        self.current_payload = bytearray()
        self.expected_crc = 0
        
        self.rx_queue: Queue = Queue(maxsize=32)
        self.tx_pending: Dict[int, UARTMessage] = {}
        
        self.tx_sequence = 0
        self.last_rx_sequence = 0
        
        self.reader_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()
        
        self.last_heartbeat_time = 0.0
        self.last_rx_time = 0.0
        
        self.stats = UARTStats()
        
        self.logger = logging.getLogger('uart_handler')
        
        self.callbacks: Dict[int, List[Callable]] = {}
    
    def connect(self) -> bool:
        """
        Connect to UART port.
        
        Returns:
            True if connected successfully
        """
        try:
            self.logger.info(f"Connecting to UART: {self.port} @ {self.baudrate} baud")
            
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=READ_TIMEOUT,
                write_timeout=1.0
            )
            
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            self.running = True
            self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self.reader_thread.start()
            
            self.connected = True
            self.last_heartbeat_time = time.time()
            self.last_rx_time = time.time()
            
            self.logger.info("UART connected successfully")
            
            self.send_heartbeat()
            
            return True
            
        except Exception as e:
            self.logger.error(f"UART connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from UART port."""
        self.logger.info("Disconnecting UART...")
        
        self.running = False
        if self.reader_thread:
            self.reader_thread.join(timeout=2.0)
        
        if self.serial:
            try:
                self.serial.close()
            except Exception as e:
                self.logger.error(f"Error closing serial port: {e}")
            self.serial = None
        
        self.connected = False
        self.logger.info("UART disconnected")
    
    def is_connected(self) -> bool:
        """
        Check if connected to ESP32.
        
        Returns:
            True if connected (received heartbeat recently)
        """
        if not self.connected:
            return False
        
        time_since_rx = time.time() - self.last_rx_time
        return time_since_rx < CONNECTION_TIMEOUT
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to UART.
        
        Returns:
            True if reconnected successfully
        """
        self.logger.info("Attempting to reconnect...")
        
        self.disconnect()
        time.sleep(1.0)
        
        return self.connect()
    
    def send_display_text(self, text: str) -> bool:
        """
        Send text to display on ESP32.
        
        Args:
            text: Text to display
            
        Returns:
            True if sent successfully
        """
        payload = text.encode('utf-8')[:MAX_PAYLOAD_SIZE]
        return self._send_message(MessageType.DISPLAY_TEXT, payload)
    
    def send_display_image(self, image_data: bytes) -> bool:
        """
        Send image data to display on ESP32.
        
        Args:
            image_data: Image bitmap data
            
        Returns:
            True if sent successfully
        """
        if len(image_data) > MAX_PAYLOAD_SIZE:
            self.logger.warning(f"Image data too large: {len(image_data)} bytes")
            return False
        
        return self._send_message(MessageType.DISPLAY_IMAGE, image_data)
    
    def send_mode_change(self, mode: int) -> bool:
        """
        Send mode change notification to ESP32.
        
        Args:
            mode: New mode (0-7)
            
        Returns:
            True if sent successfully
        """
        payload = bytes([mode])
        return self._send_message(MessageType.MODE_CHANGE, payload)
    
    def send_heartbeat(self) -> bool:
        """
        Send heartbeat to ESP32.
        
        Returns:
            True if sent successfully
        """
        uptime = int(time.time() * 1000) % (2**32)
        payload = struct.pack('>I', uptime)
        
        result = self._send_message(MessageType.HEARTBEAT, payload)
        
        if result:
            self.last_heartbeat_time = time.time()
        
        return result
    
    def send_battery_status(self, percent: int, voltage: float, charging: bool) -> bool:
        """
        Send battery status to ESP32.
        
        Args:
            percent: Battery percentage (0-100)
            voltage: Battery voltage
            charging: Charging status
            
        Returns:
            True if sent successfully
        """
        voltage_mv = int(voltage * 1000)
        payload = struct.pack('>BHB', percent, voltage_mv, 1 if charging else 0)
        
        return self._send_message(MessageType.BATTERY_STATUS, payload)
    
    def send_ack(self, sequence: int) -> bool:
        """
        Send ACK for received message.
        
        Args:
            sequence: Sequence number to acknowledge
            
        Returns:
            True if sent successfully
        """
        payload = bytes([sequence])
        result = self._send_message(MessageType.ACK, payload)
        
        if result:
            self.stats.acks_sent += 1
        
        return result
    
    def send_nack(self, sequence: int) -> bool:
        """
        Send NACK for failed message.
        
        Args:
            sequence: Sequence number to reject
            
        Returns:
            True if sent successfully
        """
        payload = bytes([sequence])
        result = self._send_message(MessageType.NACK, payload)
        
        if result:
            self.stats.nacks_sent += 1
        
        return result
    
    def available(self) -> bool:
        """
        Check if messages are available.
        
        Returns:
            True if messages in queue
        """
        return not self.rx_queue.empty()
    
    def read_message(self, timeout: float = 0.0) -> Optional[Dict[str, Any]]:
        """
        Read next message from queue.
        
        Args:
            timeout: Timeout in seconds (0 = non-blocking)
            
        Returns:
            Message dictionary or None
        """
        try:
            msg = self.rx_queue.get(timeout=timeout)
            
            return {
                'type': msg.type,
                'payload': msg.payload,
                'sequence': msg.sequence,
                'timestamp': msg.timestamp
            }
        except Empty:
            return None
    
    def register_callback(self, msg_type: int, callback: Callable) -> None:
        """
        Register callback for message type.
        
        Args:
            msg_type: Message type to listen for
            callback: Callback function(message_dict)
        """
        if msg_type not in self.callbacks:
            self.callbacks[msg_type] = []
        
        self.callbacks[msg_type].append(callback)
    
    def _send_message(self, msg_type: int, payload: bytes, needs_ack: bool = False) -> bool:
        """
        Send message with protocol framing.
        
        Args:
            msg_type: Message type
            payload: Payload data
            needs_ack: Require acknowledgment
            
        Returns:
            True if sent successfully
        """
        if not self.connected or not self.serial:
            self.logger.error("Cannot send: not connected")
            return False
        
        try:
            frame = self._build_frame(msg_type, payload)
            
            with self.lock:
                self.serial.write(frame)
                self.serial.flush()
            
            self.stats.messages_sent += 1
            self.stats.bytes_transferred += len(frame)
            
            if needs_ack:
                sequence = self._get_next_sequence()
                msg = UARTMessage(
                    type=msg_type,
                    payload=payload,
                    sequence=sequence,
                    timestamp=time.time(),
                    needs_ack=True
                )
                self.tx_pending[sequence] = msg
            
            self.logger.debug(f"Sent message type=0x{msg_type:02X} len={len(payload)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Send error: {e}")
            return False
    
    def _build_frame(self, msg_type: int, payload: bytes) -> bytes:
        """
        Build message frame with CRC.
        
        Args:
            msg_type: Message type
            payload: Payload data
            
        Returns:
            Complete frame bytes
        """
        length = len(payload)
        
        frame = bytearray()
        frame.append(START_BYTE)
        frame.append(msg_type)
        frame.append((length >> 8) & 0xFF)
        frame.append(length & 0xFF)
        
        frame.extend(payload)
        
        crc = self._calculate_crc16(frame[1:])
        
        frame.append((crc >> 8) & 0xFF)
        frame.append(crc & 0xFF)
        
        return bytes(frame)
    
    def _reader_loop(self) -> None:
        """Reader thread main loop."""
        self.logger.debug("Reader thread started")
        
        while self.running:
            try:
                if self.serial and self.serial.in_waiting > 0:
                    byte = self.serial.read(1)
                    if byte:
                        self._parse_byte(byte[0])
                else:
                    time.sleep(0.001)
                    
            except Exception as e:
                self.logger.error(f"Reader error: {e}")
                time.sleep(0.1)
        
        self.logger.debug("Reader thread stopped")
    
    def _parse_byte(self, byte: int) -> None:
        """
        Parse incoming byte through state machine.
        
        Args:
            byte: Byte to parse
        """
        if self.parser_state == ParserState.IDLE:
            if byte == START_BYTE:
                self.parser_state = ParserState.TYPE
        
        elif self.parser_state == ParserState.TYPE:
            self.current_type = byte
            self.parser_state = ParserState.LENGTH_H
        
        elif self.parser_state == ParserState.LENGTH_H:
            self.current_length = byte << 8
            self.parser_state = ParserState.LENGTH_L
        
        elif self.parser_state == ParserState.LENGTH_L:
            self.current_length |= byte
            
            if self.current_length > MAX_PAYLOAD_SIZE:
                self.logger.warning(f"Invalid length: {self.current_length}")
                self._reset_parser()
                return
            
            self.current_payload = bytearray()
            
            if self.current_length == 0:
                self.parser_state = ParserState.CRC_H
            else:
                self.parser_state = ParserState.PAYLOAD
        
        elif self.parser_state == ParserState.PAYLOAD:
            self.current_payload.append(byte)
            
            if len(self.current_payload) >= self.current_length:
                self.parser_state = ParserState.CRC_H
        
        elif self.parser_state == ParserState.CRC_H:
            self.expected_crc = byte << 8
            self.parser_state = ParserState.CRC_L
        
        elif self.parser_state == ParserState.CRC_L:
            self.expected_crc |= byte
            
            data = bytearray()
            data.append(self.current_type)
            data.append((self.current_length >> 8) & 0xFF)
            data.append(self.current_length & 0xFF)
            data.extend(self.current_payload)
            
            calculated_crc = self._calculate_crc16(data)
            
            if calculated_crc == self.expected_crc:
                self._handle_received_message()
                self.stats.messages_received += 1
            else:
                self.logger.warning(f"CRC error: expected 0x{self.expected_crc:04X}, got 0x{calculated_crc:04X}")
                self.stats.crc_errors += 1
                self.send_nack(self.last_rx_sequence)
            
            self._reset_parser()
    
    def _handle_received_message(self) -> None:
        """Handle received message after successful parsing."""
        msg_type = self.current_type
        payload = bytes(self.current_payload)
        
        self.logger.debug(f"Received message type=0x{msg_type:02X} len={len(payload)}")
        
        self.last_rx_time = time.time()
        
        if msg_type == MessageType.HEARTBEAT:
            self.last_heartbeat_time = time.time()
        
        elif msg_type == MessageType.ACK:
            if len(payload) >= 1:
                sequence = payload[0]
                self._remove_pending_message(sequence)
                self.stats.acks_received += 1
        
        elif msg_type == MessageType.NACK:
            if len(payload) >= 1:
                sequence = payload[0]
                self.stats.nacks_received += 1
        
        msg = UARTMessage(
            type=msg_type,
            payload=payload,
            timestamp=time.time()
        )
        
        try:
            self.rx_queue.put_nowait(msg)
        except:
            self.logger.warning("RX queue full, dropping message")
        
        if msg_type in self.callbacks:
            for callback in self.callbacks[msg_type]:
                try:
                    callback({
                        'type': msg.type,
                        'payload': msg.payload,
                        'timestamp': msg.timestamp
                    })
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
    
    def _reset_parser(self) -> None:
        """Reset parser to idle state."""
        self.parser_state = ParserState.IDLE
        self.current_type = 0
        self.current_length = 0
        self.current_payload = bytearray()
        self.expected_crc = 0
    
    def _calculate_crc16(self, data: bytes) -> int:
        """
        Calculate CRC16-CCITT checksum.
        
        Args:
            data: Data to checksum
            
        Returns:
            CRC16 value
        """
        crc = 0xFFFF
        
        for byte in data:
            index = ((crc >> 8) ^ byte) & 0xFF
            crc = ((crc << 8) ^ CRC16_CCITT_TABLE[index]) & 0xFFFF
        
        return crc
    
    def _get_next_sequence(self) -> int:
        """
        Get next sequence number.
        
        Returns:
            Sequence number (0-255)
        """
        self.tx_sequence = (self.tx_sequence + 1) % 256
        return self.tx_sequence
    
    def _remove_pending_message(self, sequence: int) -> None:
        """
        Remove message from pending queue.
        
        Args:
            sequence: Sequence number
        """
        if sequence in self.tx_pending:
            del self.tx_pending[sequence]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get communication statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'messages_sent': self.stats.messages_sent,
            'messages_received': self.stats.messages_received,
            'bytes_transferred': self.stats.bytes_transferred,
            'crc_errors': self.stats.crc_errors,
            'timeouts': self.stats.timeouts,
            'retries': self.stats.retries,
            'acks_sent': self.stats.acks_sent,
            'acks_received': self.stats.acks_received,
            'nacks_sent': self.stats.nacks_sent,
            'nacks_received': self.stats.nacks_received,
            'connected': self.is_connected()
        }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = UARTStats()
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        self.disconnect()


def get_message_type_name(msg_type: int) -> str:
    """
    Get human-readable name for message type.
    
    Args:
        msg_type: Message type code
        
    Returns:
        Type name string
    """
    try:
        return MessageType(msg_type).name
    except ValueError:
        return f"UNKNOWN_0x{msg_type:02X}"

