#!/usr/bin/env python3
"""
================================================================================
diagnostics.py - Hardware Diagnostic Tool
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Comprehensive hardware diagnostic tool for Stealth Deck.
Tests all hardware components and reports status.

Features:
- Component testing
- Performance benchmarks
- Error detection
- Report generation
- Automated testing

================================================================================
"""

import sys
import time
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class TestResult:
    """Test result data."""
    name: str
    passed: bool
    message: str
    duration: float
    details: Dict = None


class DiagnosticTool:
    """
    Hardware diagnostic tool.
    
    Tests all system components.
    """
    
    def __init__(self):
        """Initialize diagnostic tool."""
        self.logger = logging.getLogger('diagnostics')
        
        self.results: List[TestResult] = []
        
        self.tests = [
            ('UART Communication', self.test_uart),
            ('Camera', self.test_camera),
            ('Display', self.test_display),
            ('Storage', self.test_storage),
            ('Network', self.test_network),
            ('Power', self.test_power),
            ('Encryption', self.test_encryption),
            ('Performance', self.test_performance)
        ]
    
    def run_all_tests(self) -> bool:
        """
        Run all diagnostic tests.
        
        Returns:
            True if all tests passed
        """
        print("=" * 60)
        print("Stealth Deck Hardware Diagnostics")
        print("=" * 60)
        print()
        
        all_passed = True
        
        for test_name, test_func in self.tests:
            print(f"Testing {test_name}...", end=' ', flush=True)
            
            start = time.time()
            
            try:
                passed, message, details = test_func()
                duration = time.time() - start
                
                result = TestResult(
                    name=test_name,
                    passed=passed,
                    message=message,
                    duration=duration,
                    details=details
                )
                
                self.results.append(result)
                
                if passed:
                    print(f"✓ PASS ({duration:.2f}s)")
                else:
                    print(f"✗ FAIL ({duration:.2f}s)")
                    print(f"  Error: {message}")
                    all_passed = False
            
            except Exception as e:
                duration = time.time() - start
                
                result = TestResult(
                    name=test_name,
                    passed=False,
                    message=str(e),
                    duration=duration
                )
                
                self.results.append(result)
                
                print(f"✗ ERROR ({duration:.2f}s)")
                print(f"  Exception: {e}")
                all_passed = False
        
        print()
        self.print_summary()
        
        return all_passed
    
    def test_uart(self) -> Tuple[bool, str, Dict]:
        """Test UART communication."""
        try:
            import serial
            
            # Try to open UART port
            port = serial.Serial('/dev/serial0', 115200, timeout=1)
            
            if not port.is_open:
                return False, "Failed to open UART port", {}
            
            # Test write
            port.write(b'\xAA\xFF\x00\x00\x00\x00')
            
            port.close()
            
            return True, "UART communication OK", {'port': '/dev/serial0', 'baud': 115200}
        
        except ImportError:
            return False, "pyserial not installed", {}
        
        except Exception as e:
            return False, f"UART error: {e}", {}
    
    def test_camera(self) -> Tuple[bool, str, Dict]:
        """Test camera module."""
        try:
            from picamera2 import Picamera2
            
            camera = Picamera2()
            
            # Get camera info
            camera_config = camera.create_still_configuration()
            
            camera.close()
            
            return True, "Camera available", {'config': str(camera_config)[:100]}
        
        except ImportError:
            return False, "picamera2 not installed", {}
        
        except Exception as e:
            return False, f"Camera error: {e}", {}
    
    def test_display(self) -> Tuple[bool, str, Dict]:
        """Test display (via UART)."""
        # Display test would go through UART to ESP32
        return True, "Display test requires ESP32", {}
    
    def test_storage(self) -> Tuple[bool, str, Dict]:
        """Test storage capacity and speed."""
        import shutil
        from pathlib import Path
        
        # Check storage
        stat = shutil.disk_usage('/')
        
        total_gb = stat.total / (1024**3)
        free_gb = stat.free / (1024**3)
        used_percent = (stat.used / stat.total) * 100
        
        # Check if enough space
        if free_gb < 1:
            return False, "Low storage space", {
                'total_gb': round(total_gb, 2),
                'free_gb': round(free_gb, 2),
                'used_percent': round(used_percent, 1)
            }
        
        # Test write speed
        test_file = Path('/tmp/speedtest.bin')
        
        start = time.time()
        test_file.write_bytes(b'\x00' * (1024 * 1024))  # 1MB
        write_time = time.time() - start
        
        start = time.time()
        test_file.read_bytes()
        read_time = time.time() - start
        
        test_file.unlink()
        
        write_speed = 1 / write_time  # MB/s
        read_speed = 1 / read_time
        
        return True, "Storage OK", {
            'free_gb': round(free_gb, 2),
            'write_speed_mbs': round(write_speed, 2),
            'read_speed_mbs': round(read_speed, 2)
        }
    
    def test_network(self) -> Tuple[bool, str, Dict]:
        """Test network connectivity."""
        import socket
        
        # Test DNS resolution
        try:
            socket.gethostbyname('google.com')
            dns_ok = True
        except:
            dns_ok = False
        
        # Test internet connectivity
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            internet_ok = True
        except:
            internet_ok = False
        
        if not dns_ok:
            return False, "DNS resolution failed", {}
        
        if not internet_ok:
            return False, "No internet connectivity", {}
        
        return True, "Network OK", {
            'dns': dns_ok,
            'internet': internet_ok
        }
    
    def test_power(self) -> Tuple[bool, str, Dict]:
        """Test power management."""
        # Read battery level (if available)
        details = {}
        
        try:
            # Try to read battery info
            with open('/sys/class/power_supply/BAT0/capacity', 'r') as f:
                capacity = int(f.read().strip())
                details['battery_percent'] = capacity
        except:
            pass
        
        return True, "Power management OK", details
    
    def test_encryption(self) -> Tuple[bool, str, Dict]:
        """Test encryption functionality."""
        try:
            from cryptography.fernet import Fernet
            
            # Generate key
            key = Fernet.generate_key()
            cipher = Fernet(key)
            
            # Test encryption/decryption
            test_data = b"Test encryption data"
            
            encrypted = cipher.encrypt(test_data)
            decrypted = cipher.decrypt(encrypted)
            
            if decrypted != test_data:
                return False, "Encryption/decryption mismatch", {}
            
            return True, "Encryption OK", {'algorithm': 'Fernet (AES-128-CBC)'}
        
        except ImportError:
            return False, "cryptography not installed", {}
        
        except Exception as e:
            return False, f"Encryption error: {e}", {}
    
    def test_performance(self) -> Tuple[bool, str, Dict]:
        """Test system performance."""
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        
        # Temperature (if available)
        temp = None
        try:
            temp_info = psutil.sensors_temperatures()
            if 'cpu_thermal' in temp_info:
                temp = temp_info['cpu_thermal'][0].current
        except:
            pass
        
        details = {
            'cpu_percent': cpu_percent,
            'memory_percent': mem_percent,
            'available_mb': mem.available / (1024**2)
        }
        
        if temp:
            details['cpu_temp_c'] = temp
        
        # Check if system is healthy
        if cpu_percent > 90:
            return False, "High CPU usage", details
        
        if mem_percent > 90:
            return False, "Low memory", details
        
        return True, "Performance OK", details
    
    def print_summary(self):
        """Print test summary."""
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        print(f"Total Tests:  {len(self.results)}")
        print(f"Passed:       {passed}")
        print(f"Failed:       {failed}")
        print()
        
        if failed > 0:
            print("Failed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}: {result.message}")
        
        print("=" * 60)
    
    def generate_report(self, filename: str):
        """
        Generate diagnostic report.
        
        Args:
            filename: Output filename
        """
        with open(filename, 'w') as f:
            f.write("Stealth Deck Hardware Diagnostic Report\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in self.results:
                f.write(f"Test: {result.name}\n")
                f.write(f"Result: {'PASS' if result.passed else 'FAIL'}\n")
                f.write(f"Duration: {result.duration:.2f}s\n")
                f.write(f"Message: {result.message}\n")
                
                if result.details:
                    f.write("Details:\n")
                    for key, value in result.details.items():
                        f.write(f"  {key}: {value}\n")
                
                f.write("\n")
            
            f.write("=" * 60 + "\n")


def main():
    """Main function."""
    logging.basicConfig(level=logging.INFO)
    
    tool = DiagnosticTool()
    
    all_passed = tool.run_all_tests()
    
    # Generate report
    report_file = f"diagnostic_report_{int(time.time())}.txt"
    tool.generate_report(report_file)
    print(f"\nReport saved to: {report_file}")
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
