"""
================================================================================
pairing_manager.py - P2P Pairing Manager
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Manages device pairing and authentication for P2P transfers.
Handles key exchange, verification, and trust management.

Features:
- Device pairing
- Key exchange
- Fingerprint verification
- Trust management
- Pairing persistence

================================================================================
"""

import logging
import json
import hashlib
from typing import Optional, Dict, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
import time


@dataclass
class PairedDevice:
    """Paired device information."""
    address: str
    name: str
    public_key: str
    fingerprint: str
    paired_at: float
    last_seen: float
    trusted: bool = True


class PairingManager:
    """
    P2P pairing manager.
    
    Manages device pairing and trust relationships.
    """
    
    def __init__(self, config_dir: str = '/etc/stealth-deck'):
        """
        Initialize pairing manager.
        
        Args:
            config_dir: Configuration directory
        """
        self.logger = logging.getLogger('pairing_manager')
        
        self.config_dir = Path(config_dir)
        self.paired_devices_file = self.config_dir / 'paired_devices.json'
        
        self.paired_devices: Dict[str, PairedDevice] = {}
        
        self.pairing_callback: Optional[Callable] = None
        
        self._load_paired_devices()
    
    def initiate_pairing(self, address: str, name: str, 
                        public_key: bytes) -> Optional[str]:
        """
        Initiate device pairing.
        
        Args:
            address: Device address
            name: Device name
            public_key: Device public key
            
        Returns:
            Fingerprint for verification or None
        """
        try:
            fingerprint = self._calculate_fingerprint(public_key)
            
            device = PairedDevice(
                address=address,
                name=name,
                public_key=public_key.hex(),
                fingerprint=fingerprint,
                paired_at=time.time(),
                last_seen=time.time(),
                trusted=False  # Not trusted until verified
            )
            
            self.paired_devices[address] = device
            
            self.logger.info(f"Pairing initiated: {name} ({address})")
            self.logger.info(f"Fingerprint: {fingerprint}")
            
            if self.pairing_callback:
                self.pairing_callback(device)
            
            return fingerprint
            
        except Exception as e:
            self.logger.error(f"Pairing initiation failed: {e}")
            return None
    
    def verify_pairing(self, address: str, user_confirmed: bool) -> bool:
        """
        Verify pairing after user confirmation.
        
        Args:
            address: Device address
            user_confirmed: User confirmed fingerprint match
            
        Returns:
            True if pairing verified
        """
        if address not in self.paired_devices:
            self.logger.error(f"Device not found: {address}")
            return False
        
        if not user_confirmed:
            self.logger.info("User rejected pairing")
            del self.paired_devices[address]
            return False
        
        device = self.paired_devices[address]
        device.trusted = True
        
        self._save_paired_devices()
        
        self.logger.info(f"Pairing verified: {device.name}")
        
        return True
    
    def unpair_device(self, address: str) -> bool:
        """
        Unpair device.
        
        Args:
            address: Device address
            
        Returns:
            True if unpaired
        """
        if address not in self.paired_devices:
            return False
        
        device = self.paired_devices[address]
        
        del self.paired_devices[address]
        
        self._save_paired_devices()
        
        self.logger.info(f"Device unpaired: {device.name}")
        
        return True
    
    def is_paired(self, address: str) -> bool:
        """
        Check if device is paired.
        
        Args:
            address: Device address
            
        Returns:
            True if paired
        """
        return address in self.paired_devices
    
    def is_trusted(self, address: str) -> bool:
        """
        Check if device is trusted.
        
        Args:
            address: Device address
            
        Returns:
            True if trusted
        """
        device = self.paired_devices.get(address)
        
        return device is not None and device.trusted
    
    def get_paired_device(self, address: str) -> Optional[PairedDevice]:
        """
        Get paired device information.
        
        Args:
            address: Device address
            
        Returns:
            Device or None
        """
        return self.paired_devices.get(address)
    
    def get_all_paired_devices(self) -> list:
        """
        Get all paired devices.
        
        Returns:
            List of paired devices
        """
        return list(self.paired_devices.values())
    
    def update_last_seen(self, address: str):
        """
        Update last seen timestamp.
        
        Args:
            address: Device address
        """
        if address in self.paired_devices:
            self.paired_devices[address].last_seen = time.time()
            self._save_paired_devices()
    
    def set_pairing_callback(self, callback: Callable):
        """
        Set callback for pairing events.
        
        Args:
            callback: Callback function
        """
        self.pairing_callback = callback
    
    def _calculate_fingerprint(self, public_key: bytes) -> str:
        """
        Calculate key fingerprint.
        
        Args:
            public_key: Public key bytes
            
        Returns:
            Fingerprint string
        """
        hash_obj = hashlib.sha256(public_key)
        fingerprint_bytes = hash_obj.digest()[:8]
        
        fingerprint = fingerprint_bytes.hex().upper()
        
        formatted = ':'.join([fingerprint[i:i+2] for i in range(0, len(fingerprint), 2)])
        
        return formatted
    
    def _load_paired_devices(self):
        """Load paired devices from file."""
        try:
            if not self.paired_devices_file.exists():
                return
            
            with open(self.paired_devices_file, 'r') as f:
                data = json.load(f)
            
            for addr, device_data in data.items():
                device = PairedDevice(**device_data)
                self.paired_devices[addr] = device
            
            self.logger.info(f"Loaded {len(self.paired_devices)} paired devices")
            
        except Exception as e:
            self.logger.error(f"Load paired devices failed: {e}")
    
    def _save_paired_devices(self):
        """Save paired devices to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                addr: asdict(device)
                for addr, device in self.paired_devices.items()
            }
            
            with open(self.paired_devices_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug("Paired devices saved")
            
        except Exception as e:
            self.logger.error(f"Save paired devices failed: {e}")
    
    def export_paired_devices(self, output_file: str) -> bool:
        """
        Export paired devices to file.
        
        Args:
            output_file: Output file path
            
        Returns:
            True if successful
        """
        try:
            data = {
                addr: asdict(device)
                for addr, device in self.paired_devices.items()
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Paired devices exported to {output_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def import_paired_devices(self, input_file: str) -> bool:
        """
        Import paired devices from file.
        
        Args:
            input_file: Input file path
            
        Returns:
            True if successful
        """
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            for addr, device_data in data.items():
                device = PairedDevice(**device_data)
                self.paired_devices[addr] = device
            
            self._save_paired_devices()
            
            self.logger.info(f"Paired devices imported from {input_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Import failed: {e}")
            return False
    
    def clear_all_pairings(self):
        """Clear all paired devices."""
        self.paired_devices.clear()
        self._save_paired_devices()
        
        self.logger.info("All pairings cleared")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    pairing = PairingManager('/tmp/stealth-deck-test')
    
    # Test pairing
    test_key = b'test_public_key_12345678'
    fingerprint = pairing.initiate_pairing('AA:BB:CC:DD:EE:FF', 'Test Device', test_key)
    
    print(f"Fingerprint: {fingerprint}")
    
    # Verify pairing
    pairing.verify_pairing('AA:BB:CC:DD:EE:FF', True)
    
    # Check status
    print(f"Paired: {pairing.is_paired('AA:BB:CC:DD:EE:FF')}")
    print(f"Trusted: {pairing.is_trusted('AA:BB:CC:DD:EE:FF')}")
