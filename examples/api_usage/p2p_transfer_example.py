#!/usr/bin/env python3
"""
Example: P2P File Transfer with Stealth Deck
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'raspberry-pi'))

from src.p2p.device_discovery import DeviceDiscovery
from src.p2p.pairing_manager import PairingManager
from src.p2p.transfer_handler import TransferHandler


def main():
    """P2P transfer example."""
    
    print("Stealth Deck - P2P Transfer Example")
    print("=" * 60)
    
    # Step 1: Device Discovery
    print("\n1. Discovering devices...")
    print("-" * 60)
    
    discovery = DeviceDiscovery()
    
    devices = discovery.start_discovery(duration=5)
    
    print(f"Found {len(devices)} Stealth Deck devices:")
    for i, device in enumerate(devices):
        print(f"  {i+1}. {device.name} ({device.address})")
    
    if not devices:
        print("No devices found. Exiting.")
        return
    
    # Step 2: Pairing
    print("\n2. Pairing with device...")
    print("-" * 60)
    
    target_device = devices[0]
    
    pairing = PairingManager('/tmp/stealth-deck-example')
    
    # Simulate pairing
    public_key = b"example_public_key_12345678"
    fingerprint = pairing.initiate_pairing(
        target_device.address,
        target_device.name,
        public_key
    )
    
    print(f"Fingerprint: {fingerprint}")
    print("Verify fingerprint matches on both devices!")
    
    # Auto-confirm for example
    pairing.verify_pairing(target_device.address, True)
    
    print("✓ Devices paired successfully")
    
    # Step 3: File Transfer
    print("\n3. Transferring file...")
    print("-" * 60)
    
    # Create test file
    test_file = '/tmp/test_transfer.txt'
    with open(test_file, 'w') as f:
        f.write("Test file for P2P transfer!\n" * 100)
    
    transfer = TransferHandler(chunk_size=1024)
    
    # Prepare transfer
    metadata = transfer.prepare_send(test_file)
    
    print(f"File: {metadata.file_name}")
    print(f"Size: {metadata.file_size} bytes")
    print(f"Chunks: {metadata.chunks_total}")
    
    # Simulate transfer
    print("\nTransferring...", end='', flush=True)
    
    for i in range(metadata.chunks_total):
        chunk_data = transfer.send_chunk(i)
        
        if chunk_data:
            progress = transfer.get_progress()
            print(f"\rProgress: {progress['progress']}%", end='', flush=True)
            time.sleep(0.01)  # Simulate network delay
    
    print("\n✓ Transfer complete!")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
