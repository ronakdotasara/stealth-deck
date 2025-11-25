"""
================================================================================
device_discovery.py - P2P Device Discovery
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Discovers nearby Stealth Deck devices for P2P connections.
Uses Bluetooth device scanning and filtering.

Features:
- Bluetooth scanning
- Device filtering
- Signal strength
- Device identification
- Connection management

================================================================================
"""

import logging
import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass


@dataclass
class DiscoveredDevice:
    """Discovered device information."""
    address: str
    name: str
    rssi: int
    device_class: int
    last_seen: float


class DeviceDiscovery:
    """
    P2P device discovery manager.
    
    Discovers and tracks nearby Stealth Deck devices.
    """
    
    def __init__(self):
        """Initialize device discovery."""
        self.logger = logging.getLogger('device_discovery')
        
        self.devices: Dict[str, DiscoveredDevice] = {}
        self.scan_duration = 10
        self.device_timeout = 60
        
        self.discovery_callback: Optional[Callable] = None
        
        try:
            import bluetooth
            self.bluetooth = bluetooth
            self.bluetooth_available = True
        except ImportError:
            self.logger.warning("Bluetooth library not available")
            self.bluetooth_available = False
    
    def start_discovery(self, duration: int = 10) -> List[DiscoveredDevice]:
        """
        Start device discovery.
        
        Args:
            duration: Scan duration in seconds
            
        Returns:
            List of discovered devices
        """
        if not self.bluetooth_available:
            self.logger.error("Bluetooth not available")
            return []
        
        self.logger.info(f"Starting discovery for {duration}s...")
        
        try:
            nearby_devices = self.bluetooth.discover_devices(
                duration=duration,
                lookup_names=True,
                lookup_class=True
            )
            
            current_time = time.time()
            
            for addr, name, device_class in nearby_devices:
                if self._is_stealth_deck(name):
                    device = DiscoveredDevice(
                        address=addr,
                        name=name,
                        rssi=0,  # RSSI not available in this API
                        device_class=device_class,
                        last_seen=current_time
                    )
                    
                    self.devices[addr] = device
                    
                    if self.discovery_callback:
                        self.discovery_callback(device)
                    
                    self.logger.info(f"Found device: {name} ({addr})")
            
            self._cleanup_stale_devices()
            
            return list(self.devices.values())
            
        except Exception as e:
            self.logger.error(f"Discovery failed: {e}")
            return []
    
    def stop_discovery(self):
        """Stop device discovery."""
        self.logger.info("Discovery stopped")
    
    def get_devices(self) -> List[DiscoveredDevice]:
        """
        Get list of discovered devices.
        
        Returns:
            List of devices
        """
        self._cleanup_stale_devices()
        
        return list(self.devices.values())
    
    def get_device(self, address: str) -> Optional[DiscoveredDevice]:
        """
        Get device by address.
        
        Args:
            address: Device address
            
        Returns:
            Device or None
        """
        return self.devices.get(address)
    
    def get_closest_device(self) -> Optional[DiscoveredDevice]:
        """
        Get device with strongest signal.
        
        Returns:
            Device or None
        """
        if not self.devices:
            return None
        
        return max(self.devices.values(), key=lambda d: d.rssi)
    
    def set_discovery_callback(self, callback: Callable):
        """
        Set callback for device discovery.
        
        Args:
            callback: Callback function
        """
        self.discovery_callback = callback
    
    def _is_stealth_deck(self, name: str) -> bool:
        """
        Check if device is Stealth Deck.
        
        Args:
            name: Device name
            
        Returns:
            True if Stealth Deck
        """
        if not name:
            return False
        
        keywords = ['stealth', 'deck', 'stealthdeck']
        
        name_lower = name.lower()
        
        return any(keyword in name_lower for keyword in keywords)
    
    def _cleanup_stale_devices(self):
        """Remove devices not seen recently."""
        current_time = time.time()
        
        stale_addresses = [
            addr for addr, device in self.devices.items()
            if current_time - device.last_seen > self.device_timeout
        ]
        
        for addr in stale_addresses:
            self.logger.debug(f"Removing stale device: {addr}")
            del self.devices[addr]
    
    def clear_devices(self):
        """Clear discovered devices."""
        self.devices.clear()
        self.logger.info("Device list cleared")
    
    def get_device_count(self) -> int:
        """
        Get number of discovered devices.
        
        Returns:
            Device count
        """
        self._cleanup_stale_devices()
        
        return len(self.devices)
    
    def is_device_available(self, address: str) -> bool:
        """
        Check if device is available.
        
        Args:
            address: Device address
            
        Returns:
            True if available
        """
        device = self.get_device(address)
        
        if not device:
            return False
        
        current_time = time.time()
        
        return (current_time - device.last_seen) < self.device_timeout


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    discovery = DeviceDiscovery()
    
    def on_device_found(device):
        print(f"Found: {device.name} - {device.address}")
    
    discovery.set_discovery_callback(on_device_found)
    
    devices = discovery.start_discovery(10)
    
    print(f"\nFound {len(devices)} Stealth Deck devices")
    
    for device in devices:
        print(f"  {device.name} ({device.address})")
