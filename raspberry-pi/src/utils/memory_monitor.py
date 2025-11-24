"""
================================================================================
memory_monitor.py - Memory Monitoring for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Memory monitoring utilities for tracking and managing memory usage
on the resource-constrained Raspberry Pi Zero 2W.

Features:
- Memory usage tracking
- Memory pressure detection
- Automatic garbage collection
- Memory leak detection
- Usage alerts

================================================================================
"""

import logging
import psutil
import gc
import time
from typing import Dict, Any, Optional


class MemoryMonitor:
    """
    Memory monitoring and management for Stealth Deck.
    
    Tracks memory usage and triggers cleanup when needed.
    """
    
    def __init__(self, threshold_percent: float = 80.0):
        """
        Initialize memory monitor.
        
        Args:
            threshold_percent: Memory threshold for warnings
        """
        self.threshold_percent = threshold_percent
        self.logger = logging.getLogger('memory_monitor')
        
        self.last_check_time = 0.0
        self.check_interval = 10.0
        
        self.usage_history = []
        self.max_history_size = 100
        
        self.high_memory_count = 0
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get current memory information.
        
        Returns:
            Memory info dictionary
        """
        vm = psutil.virtual_memory()
        
        return {
            'total_mb': vm.total / (1024 * 1024),
            'available_mb': vm.available / (1024 * 1024),
            'used_mb': vm.used / (1024 * 1024),
            'percent': vm.percent,
            'free_mb': vm.free / (1024 * 1024)
        }
    
    def check_memory(self) -> bool:
        """
        Check memory usage.
        
        Returns:
            True if memory usage is high
        """
        current_time = time.time()
        
        if current_time - self.last_check_time < self.check_interval:
            return False
        
        self.last_check_time = current_time
        
        info = self.get_memory_info()
        
        self.usage_history.append({
            'timestamp': current_time,
            'percent': info['percent']
        })
        
        if len(self.usage_history) > self.max_history_size:
            self.usage_history.pop(0)
        
        is_high = info['percent'] > self.threshold_percent
        
        if is_high:
            self.high_memory_count += 1
            self.logger.warning(
                f"High memory usage: {info['percent']:.1f}% "
                f"({info['used_mb']:.1f}/{info['total_mb']:.1f} MB)"
            )
        else:
            self.high_memory_count = 0
        
        return is_high
    
    def is_high(self) -> bool:
        """
        Check if memory usage is currently high.
        
        Returns:
            True if memory usage exceeds threshold
        """
        info = self.get_memory_info()
        return info['percent'] > self.threshold_percent
    
    def force_gc(self) -> int:
        """
        Force garbage collection.
        
        Returns:
            Number of objects collected
        """
        self.logger.info("Forcing garbage collection")
        
        collected = gc.collect()
        
        self.logger.info(f"Garbage collection freed {collected} objects")
        
        return collected
    
    def get_average_usage(self, window: int = 10) -> float:
        """
        Get average memory usage over recent history.
        
        Args:
            window: Number of samples to average
            
        Returns:
            Average memory usage percentage
        """
        if not self.usage_history:
            return 0.0
        
        recent = self.usage_history[-window:]
        return sum(h['percent'] for h in recent) / len(recent)
    
    def get_peak_usage(self) -> float:
        """
        Get peak memory usage from history.
        
        Returns:
            Peak memory usage percentage
        """
        if not self.usage_history:
            return 0.0
        
        return max(h['percent'] for h in self.usage_history)
    
    def clear_history(self) -> None:
        """Clear usage history."""
        self.usage_history.clear()
        self.logger.debug("Memory usage history cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Statistics dictionary
        """
        info = self.get_memory_info()
        
        return {
            'current': info,
            'average': self.get_average_usage(),
            'peak': self.get_peak_usage(),
            'threshold': self.threshold_percent,
            'high_count': self.high_memory_count,
            'history_size': len(self.usage_history)
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    monitor = MemoryMonitor(threshold_percent=80.0)
    
    info = monitor.get_memory_info()
    print(f"Memory: {info['used_mb']:.1f}/{info['total_mb']:.1f} MB ({info['percent']:.1f}%)")
    
    if monitor.is_high():
        print("Memory usage is high!")
        monitor.force_gc()

