"""
================================================================================
bluetooth_manager.py - Bluetooth Manager for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Bluetooth manager for P2P file transfer and device communication.
Handles pairing, connection, and data transfer via Bluetooth SPP.

Features:
- Device discovery
- Pairing management
- SPP connection
- Data transfer
- Connection monitoring

================================================================================
"""

import logging
import time
import subprocess
from typing import Optional, List, Dict, Any, Callable
import bluetooth


class BluetoothManager:
    """
    Bluetooth manager for P2P communication.
    
    Manages Bluetooth connections and data transfer.
    """
    
    def __init__(self):
        """Initialize Bluetooth manager."""
        self.logger = logging.getLogger('bluetooth_manager')
        
        self.device_name = "StealthDeck"
        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        
        self.server_sock: Optional[bluetooth.BluetoothSocket] = None
        self.client_sock: Optional[bluetooth.BluetoothSocket] = None
        
        self.connected = False
        self.connected_device = None
        
        self.known_devices: Dict[str, str] = {}
        
        self.receive_callback: Optional[Callable] = None
    
    def initialize(self) -> bool:
        """
        Initialize Bluetooth adapter.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info("Initializing Bluetooth...")
            
            self._enable_bluetooth()
            
            self._set_device_name()
            
            self.logger.info("Bluetooth initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Bluetooth initialization failed: {e}")
            return False
    
    def start_server(self) -> bool:
        """
        Start Bluetooth server.
        
        Returns:
            True if started
        """
        try:
            self.logger.info("Starting Bluetooth server...")
            
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            self.server_sock.bind(("", bluetooth.PORT_ANY))
            self.server_sock.listen(1)
            
            port = self.server_sock.getsockname()[1]
            
            bluetooth.advertise_service(
                self.server_sock,
                self.device_name,
                service_id=self.uuid,
                service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
                profiles=[bluetooth.SERIAL_PORT_PROFILE]
            )
            
            self.logger.info(f"Bluetooth server started on port {port}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    def accept_connection(self, timeout: float = 30.0) -> bool:
        """
        Accept incoming connection.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if connected
        """
        try:
            self.logger.info("Waiting for connection...")
            
            self.server_sock.settimeout(timeout)
            
            self.client_sock, client_info = self.server_sock.accept()
            
            self.connected = True
            self.connected_device = client_info
            
            self.logger.info(f"Connected to {client_info}")
            
            return True
            
        except bluetooth.BluetoothError as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def connect_to_device(self, address: str, port: int = 1) -> bool:
        """
        Connect to remote device.
        
        Args:
            address: Bluetooth MAC address
            port: RFCOMM port
            
        Returns:
            True if connected
        """
        try:
            self.logger.info(f"Connecting to {address}:{port}...")
            
            self.client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            self.client_sock.connect((address, port))
            
            self.connected = True
            self.connected_device = address
            
            self.logger.info(f"Connected to {address}")
            
            return True
            
        except bluetooth.BluetoothError as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from device."""
        try:
            if self.client_sock:
                self.client_sock.close()
                self.client_sock = None
            
            self.connected = False
            self.connected_device = None
            
            self.logger.info("Disconnected")
            
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
    
    def disconnect_all(self) -> None:
        """Disconnect all connections."""
        self.disconnect()
        
        if self.server_sock:
            try:
                self.server_sock.close()
            except:
                pass
            self.server_sock = None
    
    def send_data(self, data: bytes) -> bool:
        """
        Send data to connected device.
        
        Args:
            data: Data bytes to send
            
        Returns:
            True if sent
        """
        if not self.connected or not self.client_sock:
            self.logger.error("Not connected")
            return False
        
        try:
            self.client_sock.send(data)
            return True
            
        except Exception as e:
            self.logger.error(f"Send failed: {e}")
            self.disconnect()
            return False
    
    def receive_data(self, buffer_size: int = 1024) -> Optional[bytes]:
        """
        Receive data from connected device.
        
        Args:
            buffer_size: Buffer size
            
        Returns:
            Received data or None
        """
        if not self.connected or not self.client_sock:
            return None
        
        try:
            data = self.client_sock.recv(buffer_size)
            return data
            
        except Exception as e:
            self.logger.error(f"Receive failed: {e}")
            self.disconnect()
            return None
    
    def discover_devices(self, duration: int = 8) -> List[Dict[str, str]]:
        """
        Discover nearby Bluetooth devices.
        
        Args:
            duration: Scan duration in seconds
            
        Returns:
            List of discovered devices
        """
        try:
            self.logger.info(f"Discovering devices ({duration}s)...")
            
            nearby_devices = bluetooth.discover_devices(
                duration=duration,
                lookup_names=True
            )
            
            devices = []
            for addr, name in nearby_devices:
                devices.append({
                    'address': addr,
                    'name': name or 'Unknown'
                })
            
            self.logger.info(f"Found {len(devices)} devices")
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Discovery failed: {e}")
            return []
    
    def is_connected(self) -> bool:
        """
        Check if connected.
        
        Returns:
            True if connected
        """
        return self.connected
    
    def get_connected_device(self) -> Optional[str]:
        """
        Get connected device info.
        
        Returns:
            Device address or None
        """
        return self.connected_device
    
    def _enable_bluetooth(self) -> None:
        """Enable Bluetooth adapter."""
        try:
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], 
                         check=True, timeout=5)
        except Exception as e:
            self.logger.warning(f"Could not enable Bluetooth: {e}")
    
    def _set_device_name(self) -> None:
        """Set Bluetooth device name."""
        try:
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'name', self.device_name],
                         check=True, timeout=5)
        except Exception as e:
            self.logger.warning(f"Could not set device name: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    bt = BluetoothManager()
    
    if bt.initialize():
        devices = bt.discover_devices(duration=5)
        
        for device in devices:
            print(f"Found: {device['name']} ({device['address']})")
