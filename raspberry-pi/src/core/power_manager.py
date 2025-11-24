"""
================================================================================
power_manager.py - Power Management for Raspberry Pi
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Power management for Raspberry Pi Zero 2W to optimize battery life.
Controls CPU frequency, throttling, and power modes.

Features:
- CPU frequency scaling
- Power mode management
- Temperature monitoring
- Thermal throttling
- Battery optimization

================================================================================
"""

import logging
import os
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path


class PowerMode:
    """Power mode constants."""
    IDLE = 'idle'
    NORMAL = 'normal'
    ACTIVE = 'active'
    PERFORMANCE = 'performance'


class PowerManager:
    """
    Power manager for Raspberry Pi.
    
    Manages CPU frequency, thermal throttling, and power optimization.
    """
    
    def __init__(self):
        """Initialize power manager."""
        self.logger = logging.getLogger('power_manager')
        
        self.current_mode = PowerMode.NORMAL
        
        self.cpu_freq_path = Path('/sys/devices/system/cpu/cpu0/cpufreq')
        self.thermal_path = Path('/sys/class/thermal/thermal_zone0')
        
        self.freq_min = 600000
        self.freq_max = 1000000
        self.freq_normal = 800000
        
        self.throttle_temp = 70.0
        self.critical_temp = 80.0
        
        self.is_throttled = False
    
    def set_mode(self, mode: str) -> bool:
        """
        Set power mode.
        
        Args:
            mode: Power mode (idle, normal, active, performance)
            
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Setting power mode: {mode}")
            
            if mode == PowerMode.IDLE:
                self.set_cpu_frequency(self.freq_min)
            elif mode == PowerMode.NORMAL:
                self.set_cpu_frequency(self.freq_normal)
            elif mode == PowerMode.ACTIVE:
                self.set_cpu_frequency(self.freq_max)
            elif mode == PowerMode.PERFORMANCE:
                self.set_governor('performance')
            else:
                self.logger.warning(f"Unknown power mode: {mode}")
                return False
            
            self.current_mode = mode
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set power mode: {e}")
            return False
    
    def set_cpu_frequency(self, freq_khz: int) -> bool:
        """
        Set CPU frequency.
        
        Args:
            freq_khz: Frequency in kHz
            
        Returns:
            True if successful
        """
        try:
            freq_khz = max(self.freq_min, min(self.freq_max, freq_khz))
            
            scaling_file = self.cpu_freq_path / 'scaling_setspeed'
            
            if not scaling_file.exists():
                self.logger.warning("CPU frequency scaling not available")
                return False
            
            with open(scaling_file, 'w') as f:
                f.write(str(freq_khz))
            
            self.logger.debug(f"CPU frequency set to {freq_khz} kHz")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set CPU frequency: {e}")
            return False
    
    def get_cpu_frequency(self) -> int:
        """
        Get current CPU frequency.
        
        Returns:
            Frequency in kHz
        """
        try:
            freq_file = self.cpu_freq_path / 'scaling_cur_freq'
            
            if freq_file.exists():
                with open(freq_file, 'r') as f:
                    return int(f.read().strip())
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to read CPU frequency: {e}")
            return 0
    
    def set_governor(self, governor: str) -> bool:
        """
        Set CPU governor.
        
        Args:
            governor: Governor name (ondemand, performance, powersave)
            
        Returns:
            True if successful
        """
        try:
            gov_file = self.cpu_freq_path / 'scaling_governor'
            
            if not gov_file.exists():
                self.logger.warning("CPU governor control not available")
                return False
            
            with open(gov_file, 'w') as f:
                f.write(governor)
            
            self.logger.info(f"CPU governor set to: {governor}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set governor: {e}")
            return False
    
    def get_cpu_temperature(self) -> float:
        """
        Get CPU temperature.
        
        Returns:
            Temperature in Celsius
        """
        try:
            temp_file = self.thermal_path / 'temp'
            
            if temp_file.exists():
                with open(temp_file, 'r') as f:
                    temp_millidegrees = int(f.read().strip())
                    return temp_millidegrees / 1000.0
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Failed to read temperature: {e}")
            return 0.0
    
    def check_thermal_throttle(self) -> bool:
        """
        Check if thermal throttling is needed.
        
        Returns:
            True if throttling applied
        """
        temp = self.get_cpu_temperature()
        
        if temp > self.critical_temp:
            self.logger.warning(f"Critical temperature: {temp:.1f}°C")
            self.set_mode(PowerMode.IDLE)
            self.is_throttled = True
            return True
        
        elif temp > self.throttle_temp:
            if not self.is_throttled:
                self.logger.warning(f"High temperature: {temp:.1f}°C - throttling")
                self.throttle_cpu()
                self.is_throttled = True
            return True
        
        else:
            if self.is_throttled:
                self.logger.info("Temperature normalized - unthrottling")
                self.set_mode(PowerMode.NORMAL)
                self.is_throttled = False
            return False
    
    def throttle_cpu(self) -> None:
        """Apply CPU throttling."""
        reduced_freq = int(self.freq_max * 0.7)
        self.set_cpu_frequency(reduced_freq)
    
    def get_voltage(self) -> float:
        """
        Get core voltage.
        
        Returns:
            Voltage in volts
        """
        try:
            result = subprocess.run(
                ['vcgencmd', 'measure_volts', 'core'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                voltage_str = result.stdout.strip().split('=')[1].rstrip('V')
                return float(voltage_str)
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Failed to read voltage: {e}")
            return 0.0
    
    def get_power_info(self) -> Dict[str, Any]:
        """
        Get comprehensive power information.
        
        Returns:
            Power info dictionary
        """
        return {
            'mode': self.current_mode,
            'cpu_freq_khz': self.get_cpu_frequency(),
            'temperature_c': self.get_cpu_temperature(),
            'voltage_v': self.get_voltage(),
            'throttled': self.is_throttled
        }
    
    def optimize_for_battery(self) -> None:
        """Apply battery optimization settings."""
        self.logger.info("Applying battery optimizations")
        
        self.set_governor('powersave')
        
        self.set_mode(PowerMode.IDLE)
        
        try:
            subprocess.run(['sudo', 'hdparm', '-B', '1', '-S', '12', '/dev/mmcblk0'], 
                         check=False, timeout=5)
        except:
            pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    pm = PowerManager()
    
    info = pm.get_power_info()
    print(f"CPU: {info['cpu_freq_khz']} kHz")
    print(f"Temp: {info['temperature_c']:.1f}°C")
    print(f"Voltage: {info['voltage_v']:.2f}V")
    
    pm.check_thermal_throttle()
