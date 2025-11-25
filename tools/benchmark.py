#!/usr/bin/env python3
"""
================================================================================
benchmark.py - Performance Benchmark Tool
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Benchmarks system performance for various operations.
Measures throughput, latency, and resource usage.

Features:
- UART throughput testing
- Image processing benchmarks
- Encryption performance
- AI response time
- Memory usage tracking

================================================================================
"""

import time
import sys
import psutil
import os
from typing import Dict, Callable
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """Benchmark result data."""
    name: str
    duration: float
    operations: int
    throughput: float
    memory_mb: float
    cpu_percent: float


class PerformanceBenchmark:
    """
    Performance benchmarking tool.
    
    Measures system performance metrics.
    """
    
    def __init__(self):
        """Initialize benchmark tool."""
        self.results = []
        self.process = psutil.Process(os.getpid())
    
    def run_benchmark(self, name: str, func: Callable, iterations: int = 1000) -> BenchmarkResult:
        """
        Run benchmark function.
        
        Args:
            name: Benchmark name
            func: Function to benchmark
            iterations: Number of iterations
            
        Returns:
            Benchmark result
        """
        print(f"Running benchmark: {name}...", end=' ', flush=True)
        
        # Record initial state
        self.process.cpu_percent()  # Initialize
        initial_memory = self.process.memory_info().rss / (1024 * 1024)
        
        # Run benchmark
        start = time.time()
        
        for _ in range(iterations):
            func()
        
        duration = time.time() - start
        
        # Record final state
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        cpu_percent = self.process.cpu_percent()
        
        # Calculate metrics
        throughput = iterations / duration
        memory_used = final_memory - initial_memory
        
        result = BenchmarkResult(
            name=name,
            duration=duration,
            operations=iterations,
            throughput=throughput,
            memory_mb=memory_used,
            cpu_percent=cpu_percent
        )
        
        self.results.append(result)
        
        print(f"Done ({duration:.2f}s, {throughput:.0f} ops/sec)")
        
        return result
    
    def benchmark_uart_throughput(self):
        """Benchmark UART throughput."""
        # Simulate UART message creation
        def create_message():
            msg_type = 0x01
            payload = b"Test message" * 10
            length = len(payload)
            
            message = bytes([0xAA, msg_type]) + \
                     length.to_bytes(2, 'big') + \
                     payload + \
                     b'\x00\x00'  # CRC placeholder
            
            return message
        
        self.run_benchmark("UART Message Creation", create_message, 10000)
    
    def benchmark_crc_calculation(self):
        """Benchmark CRC calculation."""
        test_data = b"Test data for CRC calculation" * 10
        
        def calculate_crc():
            crc = 0xFFFF
            for byte in test_data:
                crc ^= byte << 8
                for _ in range(8):
                    if crc & 0x8000:
                        crc = (crc << 1) ^ 0x1021
                    else:
                        crc = crc << 1
                    crc &= 0xFFFF
            return crc
        
        self.run_benchmark("CRC16 Calculation", calculate_crc, 10000)
    
    def benchmark_encryption(self):
        """Benchmark encryption performance."""
        try:
            from cryptography.fernet import Fernet
            
            key = Fernet.generate_key()
            cipher = Fernet(key)
            
            test_data = b"Test encryption data" * 50
            
            def encrypt_decrypt():
                encrypted = cipher.encrypt(test_data)
                decrypted = cipher.decrypt(encrypted)
                return decrypted
            
            self.run_benchmark("Encryption/Decryption", encrypt_decrypt, 1000)
        
        except ImportError:
            print("Skipping encryption benchmark (cryptography not installed)")
    
    def benchmark_image_processing(self):
        """Benchmark image processing."""
        try:
            from PIL import Image
            
            # Create test image
            img = Image.new('RGB', (1640, 1232), color='blue')
            
            def resize_image():
                resized = img.resize((640, 480), Image.LANCZOS)
                return resized
            
            self.run_benchmark("Image Resize", resize_image, 100)
        
        except ImportError:
            print("Skipping image benchmark (PIL not installed)")
    
    def benchmark_json_parsing(self):
        """Benchmark JSON parsing."""
        import json
        
        test_json = json.dumps({
            'name': 'Stealth Deck',
            'version': '0.5.0',
            'features': ['AI', 'Camera', 'Security'] * 10,
            'data': {'key' + str(i): 'value' + str(i) for i in range(100)}
        })
        
        def parse_json():
            data = json.loads(test_json)
            return data
        
        self.run_benchmark("JSON Parsing", parse_json, 10000)
    
    def benchmark_text_processing(self):
        """Benchmark text processing."""
        test_text = "This is a test sentence. " * 100
        
        def process_text():
            words = test_text.split()
            word_count = len(words)
            uppercase = test_text.upper()
            return word_count
        
        self.run_benchmark("Text Processing", process_text, 10000)
    
    def benchmark_file_io(self):
        """Benchmark file I/O."""
        import tempfile
        
        test_data = b'\x00' * (1024 * 1024)  # 1MB
        
        def file_write_read():
            with tempfile.NamedTemporaryFile(delete=False) as f:
                filename = f.name
                f.write(test_data)
            
            with open(filename, 'rb') as f:
                data = f.read()
            
            os.unlink(filename)
            return len(data)
        
        self.run_benchmark("File I/O (1MB)", file_write_read, 100)
    
    def benchmark_memory_allocation(self):
        """Benchmark memory allocation."""
        def allocate_memory():
            data = [i for i in range(10000)]
            return len(data)
        
        self.run_benchmark("Memory Allocation", allocate_memory, 1000)
    
    def print_results(self):
        """Print benchmark results."""
        print("\n" + "=" * 80)
        print("Benchmark Results")
        print("=" * 80)
        print()
        
        print(f"{'Benchmark':<30} {'Duration':<10} {'Throughput':<15} {'Memory':<10} {'CPU'}")
        print("-" * 80)
        
        for result in self.results:
            print(f"{result.name:<30} "
                  f"{result.duration:>8.2f}s "
                  f"{result.throughput:>12.0f} ops/s "
                  f"{result.memory_mb:>7.1f} MB "
                  f"{result.cpu_percent:>6.1f}%")
        
        print("=" * 80)
    
    def generate_report(self, filename: str):
        """
        Generate benchmark report.
        
        Args:
            filename: Output filename
        """
        import platform
        
        with open(filename, 'w') as f:
            f.write("Stealth Deck Performance Benchmark Report\n")
            f.write("=" * 80 + "\n\n")
            
            # System info
            f.write("System Information:\n")
            f.write(f"  Platform: {platform.system()} {platform.release()}\n")
            f.write(f"  Processor: {platform.processor()}\n")
            f.write(f"  Python: {platform.python_version()}\n")
            f.write(f"  CPU Cores: {psutil.cpu_count()}\n")
            
            mem = psutil.virtual_memory()
            f.write(f"  Total Memory: {mem.total / (1024**3):.2f} GB\n")
            f.write("\n")
            
            # Benchmark results
            f.write("Benchmark Results:\n")
            f.write("-" * 80 + "\n\n")
            
            for result in self.results:
                f.write(f"Benchmark: {result.name}\n")
                f.write(f"  Duration:     {result.duration:.2f} seconds\n")
                f.write(f"  Operations:   {result.operations}\n")
                f.write(f"  Throughput:   {result.throughput:.0f} ops/sec\n")
                f.write(f"  Memory Used:  {result.memory_mb:.1f} MB\n")
                f.write(f"  CPU Usage:    {result.cpu_percent:.1f}%\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")


def main():
    """Main function."""
    print("Stealth Deck Performance Benchmark")
    print("=" * 80)
    print()
    
    benchmark = PerformanceBenchmark()
    
    # Run all benchmarks
    benchmark.benchmark_uart_throughput()
    benchmark.benchmark_crc_calculation()
    benchmark.benchmark_encryption()
    benchmark.benchmark_image_processing()
    benchmark.benchmark_json_parsing()
    benchmark.benchmark_text_processing()
    benchmark.benchmark_file_io()
    benchmark.benchmark_memory_allocation()
    
    # Print results
    benchmark.print_results()
    
    # Generate report
    report_file = f"benchmark_report_{int(time.time())}.txt"
    benchmark.generate_report(report_file)
    print(f"\nReport saved to: {report_file}")


if __name__ == '__main__':
    main()
