"""
================================================================================
network_utils.py - Network Utility Functions
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Network utility functions for connectivity checks and network operations.

Features:
- Connection testing
- IP address utilities
- Network interface info
- DNS resolution
- Bandwidth testing

================================================================================
"""

import logging
import socket
import subprocess
from typing import Optional, Dict, List
import re


class NetworkUtils:
    """
    Network utility functions.
    
    Provides network-related helper functions.
    """
    
    @staticmethod
    def is_connected(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
        """
        Check if internet is available.
        
        Args:
            host: Test host (Google DNS by default)
            port: Test port
            timeout: Timeout in seconds
            
        Returns:
            True if connected
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_local_ip() -> Optional[str]:
        """
        Get local IP address.
        
        Returns:
            IP address or None
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None
    
    @staticmethod
    def get_hostname() -> Optional[str]:
        """
        Get system hostname.
        
        Returns:
            Hostname or None
        """
        try:
            return socket.gethostname()
        except Exception:
            return None
    
    @staticmethod
    def resolve_hostname(hostname: str) -> Optional[str]:
        """
        Resolve hostname to IP.
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            IP address or None
        """
        try:
            return socket.gethostbyname(hostname)
        except Exception:
            return None
    
    @staticmethod
    def get_network_interfaces() -> Dict[str, str]:
        """
        Get network interface information.
        
        Returns:
            Dictionary of interface names to IP addresses
        """
        interfaces = {}
        
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            current_interface = None
            
            for line in result.stdout.split('\n'):
                # Interface name
                if re.match(r'^\d+:', line):
                    match = re.search(r'^\d+:\s+(\w+):', line)
                    if match:
                        current_interface = match.group(1)
                
                # IP address
                elif 'inet ' in line and current_interface:
                    match = re.search(r'inet\s+([\d.]+)', line)
                    if match:
                        interfaces[current_interface] = match.group(1)
            
        except Exception as e:
            logging.error(f"Get network interfaces failed: {e}")
        
        return interfaces
    
    @staticmethod
    def get_wifi_status() -> Dict[str, any]:
        """
        Get WiFi connection status.
        
        Returns:
            WiFi status dictionary
        """
        status = {
            'connected': False,
            'ssid': None,
            'signal_level': 0,
            'frequency': None
        }
        
        try:
            result = subprocess.run(
                ['iwconfig'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout
            
            # Check if connected
            if 'ESSID:' in output:
                ssid_match = re.search(r'ESSID:"([^"]+)"', output)
                if ssid_match:
                    status['connected'] = True
                    status['ssid'] = ssid_match.group(1)
            
            # Signal level
            signal_match = re.search(r'Signal level=(-?\d+)', output)
            if signal_match:
                status['signal_level'] = int(signal_match.group(1))
            
            # Frequency
            freq_match = re.search(r'Frequency:([\d.]+)\s+GHz', output)
            if freq_match:
                status['frequency'] = float(freq_match.group(1))
            
        except Exception as e:
            logging.error(f"Get WiFi status failed: {e}")
        
        return status
    
    @staticmethod
    def ping(host: str, count: int = 4) -> Dict[str, any]:
        """
        Ping host and get statistics.
        
        Args:
            host: Host to ping
            count: Number of pings
            
        Returns:
            Ping statistics
        """
        result = {
            'success': False,
            'packets_sent': count,
            'packets_received': 0,
            'packet_loss': 100.0,
            'min_rtt': 0.0,
            'avg_rtt': 0.0,
            'max_rtt': 0.0
        }
        
        try:
            output = subprocess.run(
                ['ping', '-c', str(count), host],
                capture_output=True,
                text=True,
                timeout=count + 5
            )
            
            if output.returncode == 0:
                result['success'] = True
                
                # Parse output
                stats_match = re.search(
                    r'(\d+) packets transmitted, (\d+) received',
                    output.stdout
                )
                
                if stats_match:
                    result['packets_sent'] = int(stats_match.group(1))
                    result['packets_received'] = int(stats_match.group(2))
                    
                    if result['packets_sent'] > 0:
                        result['packet_loss'] = (
                            (result['packets_sent'] - result['packets_received']) 
                            / result['packets_sent'] * 100
                        )
                
                # Parse RTT
                rtt_match = re.search(
                    r'min/avg/max[^=]+=\s*([\d.]+)/([\d.]+)/([\d.]+)',
                    output.stdout
                )
                
                if rtt_match:
                    result['min_rtt'] = float(rtt_match.group(1))
                    result['avg_rtt'] = float(rtt_match.group(2))
                    result['max_rtt'] = float(rtt_match.group(3))
            
        except Exception as e:
            logging.error(f"Ping failed: {e}")
        
        return result
    
    @staticmethod
    def get_mac_address(interface: str = 'wlan0') -> Optional[str]:
        """
        Get MAC address of interface.
        
        Args:
            interface: Network interface name
            
        Returns:
            MAC address or None
        """
        try:
            with open(f'/sys/class/net/{interface}/address', 'r') as f:
                mac = f.read().strip()
                return mac.upper()
        except Exception:
            return None
    
    @staticmethod
    def is_port_open(host: str, port: int, timeout: int = 2) -> bool:
        """
        Check if port is open on host.
        
        Args:
            host: Host to check
            port: Port number
            timeout: Timeout in seconds
            
        Returns:
            True if port is open
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def get_public_ip() -> Optional[str]:
        """
        Get public IP address.
        
        Returns:
            Public IP or None
        """
        try:
            import requests
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text
        except Exception:
            return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test connectivity
    print(f"Connected: {NetworkUtils.is_connected()}")
    
    # Get local IP
    print(f"Local IP: {NetworkUtils.get_local_ip()}")
    
    # Get hostname
    print(f"Hostname: {NetworkUtils.get_hostname()}")
    
    # Get interfaces
    interfaces = NetworkUtils.get_network_interfaces()
    print(f"Interfaces: {interfaces}")
    
    # WiFi status
    wifi = NetworkUtils.get_wifi_status()
    print(f"WiFi: {wifi}")
    
    # Ping test
    ping_result = NetworkUtils.ping('8.8.8.8', 3)
    print(f"Ping: {ping_result}")
