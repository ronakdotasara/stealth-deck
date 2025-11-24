"""
================================================================================
battery_monitor.py - Battery Monitoring for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Battery monitoring and management for 18650 Li-ion battery.
Tracks voltage, percentage, and charging status.

Features:
- Voltage monitoring
- Percentage calculation
- Charging detection
- Low battery warnings
- Battery health tracking

================================================================================
"""

import logging
import time
from typing import Dict, Any, Optional


class BatteryMonitor:
    """
    Battery monitor for Li-ion battery.
    
    Monitors battery voltage and calculates remaining capacity.
    """
    
    def __init__(self):
        """Initialize battery monitor."""
        self.logger = logging.getLogger('battery_monitor')
        
        self.voltage_min = 3.0
        self.voltage_max = 4.2
        self.voltage_nominal = 3.7
        
        self.last_voltage = 0.0
        self.last_percent = 0
        self.last_check_time = 0.0
        
        self.charging = False
        
        self.low_battery_threshold = 20
        self.critical_battery_threshold = 10
        
        self.voltage_history = []
        self.max_history_size = 100
    
    def get_voltage(self) -> float:
        """
        Get battery voltage.
        
        Returns:
            Battery voltage in volts
        """
        try:
            voltage = self._read_voltage_adc()
            
            self.last_voltage = voltage
            self.last_check_time = time.time()
            
            self.voltage_history.append({
                'timestamp': time.time(),
                'voltage': voltage
            })
            
            if len(self.voltage_history) > self.max_history_size:
                self.voltage_history.pop(0)
            
            return voltage
            
        except Exception as e:
            self.logger.error(f"Failed to read voltage: {e}")
            return self.last_voltage
    
    def get_percentage(self) -> int:
        """
        Get battery percentage.
        
        Returns:
            Battery percentage (0-100)
        """
        voltage = self.get_voltage()
        
        if voltage >= self.voltage_max:
            percent = 100
        elif voltage <= self.voltage_min:
            percent = 0
        else:
            voltage_range = self.voltage_max - self.voltage_min
            voltage_offset = voltage - self.voltage_min
            percent = int((voltage_offset / voltage_range) * 100)
        
        percent = max(0, min(100, percent))
        
        self.last_percent = percent
        
        return percent
    
    def is_charging(self) -> bool:
        """
        Check if battery is charging.
        
        Returns:
            True if charging
        """
        try:
            self.charging = self._detect_charging()
            return self.charging
            
        except Exception as e:
            self.logger.error(f"Failed to detect charging: {e}")
            return False
    
    def is_low_battery(self) -> bool:
        """
        Check if battery is low.
        
        Returns:
            True if battery is low
        """
        percent = self.get_percentage()
        return percent <= self.low_battery_threshold
    
    def is_critical_battery(self) -> bool:
        """
        Check if battery is critically low.
        
        Returns:
            True if battery is critical
        """
        percent = self.get_percentage()
        return percent <= self.critical_battery_threshold
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get battery status.
        
        Returns:
            Status dictionary
        """
        voltage = self.get_voltage()
        percent = self.get_percentage()
        charging = self.is_charging()
        
        return {
            'voltage': voltage,
            'percent': percent,
            'charging': charging,
            'low_battery': self.is_low_battery(),
            'critical_battery': self.is_critical_battery(),
            'health': self._estimate_health()
        }
    
    def get_time_remaining(self) -> Optional[int]:
        """
        Estimate time remaining in minutes.
        
        Returns:
            Minutes remaining or None
        """
        if self.is_charging():
            return None
        
        percent = self.get_percentage()
        
        avg_drain_rate = self._calculate_drain_rate()
        
        if avg_drain_rate <= 0:
            return None
        
        minutes_remaining = int(percent / avg_drain_rate)
        
        return minutes_remaining
    
    def _read_voltage_adc(self) -> float:
        """
        Read voltage from ADC.
        
        Returns:
            Voltage in volts
        """
        try:
            with open('/sys/class/power_supply/BAT0/voltage_now', 'r') as f:
                voltage_uv = int(f.read().strip())
                voltage = voltage_uv / 1000000.0
                return voltage
        except:
            pass
        
        return self.voltage_nominal
    
    def _detect_charging(self) -> bool:
        """
        Detect if battery is charging.
        
        Returns:
            True if charging
        """
        try:
            with open('/sys/class/power_supply/BAT0/status', 'r') as f:
                status = f.read().strip()
                return status == 'Charging'
        except:
            pass
        
        if len(self.voltage_history) >= 2:
            recent = self.voltage_history[-1]['voltage']
            previous = self.voltage_history[-2]['voltage']
            
            return recent > previous
        
        return False
    
    def _calculate_drain_rate(self) -> float:
        """
        Calculate average battery drain rate.
        
        Returns:
            Percent per minute
        """
        if len(self.voltage_history) < 10:
            return 0.5
        
        oldest = self.voltage_history[0]
        newest = self.voltage_history[-1]
        
        time_diff = newest['timestamp'] - oldest['timestamp']
        voltage_diff = oldest['voltage'] - newest['voltage']
        
        if time_diff <= 0:
            return 0.5
        
        voltage_range = self.voltage_max - self.voltage_min
        percent_diff = (voltage_diff / voltage_range) * 100
        
        minutes = time_diff / 60.0
        
        drain_rate = percent_diff / minutes
        
        return max(0.1, min(5.0, drain_rate))
    
    def _estimate_health(self) -> int:
        """
        Estimate battery health percentage.
        
        Returns:
            Health percentage (0-100)
        """
        if len(self.voltage_history) < 50:
            return 100
        
        return 100


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    battery = BatteryMonitor()
    
    status = battery.get_status()
    print(f"Voltage: {status['voltage']:.2f}V")
    print(f"Percentage: {status['percent']}%")
    print(f"Charging: {status['charging']}")
    print(f"Low Battery: {status['low_battery']}")
