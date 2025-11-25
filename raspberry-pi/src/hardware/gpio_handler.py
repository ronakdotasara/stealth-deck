"""
================================================================================
gpio_handler.py - GPIO Control Handler
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
GPIO control for Raspberry Pi peripherals.
Manages GPIO pins for status LEDs, buttons, and other hardware.

Features:
- Pin configuration
- Input/output control
- PWM support
- Interrupt handling
- Safety checks

================================================================================
"""

import logging
from typing import Optional, Callable
from enum import Enum

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available - running in simulation mode")


class PinMode(Enum):
    """Pin mode enumeration."""
    INPUT = 'input'
    OUTPUT = 'output'
    PWM = 'pwm'


class PullMode(Enum):
    """Pull resistor mode."""
    NONE = 'none'
    UP = 'up'
    DOWN = 'down'


class GPIOHandler:
    """
    GPIO control handler.
    
    Manages GPIO pins for various peripherals.
    """
    
    def __init__(self):
        """Initialize GPIO handler."""
        self.logger = logging.getLogger('gpio_handler')
        
        self.initialized = False
        self.pins_configured = {}
        self.pwm_instances = {}
        
        if GPIO_AVAILABLE:
            self._setup_gpio()
        else:
            self.logger.warning("Running in simulation mode")
    
    def _setup_gpio(self):
        """Setup GPIO library."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            self.initialized = True
            self.logger.info("GPIO initialized (BCM mode)")
            
        except Exception as e:
            self.logger.error(f"GPIO setup failed: {e}")
    
    def setup_pin(self, pin: int, mode: PinMode, 
                  pull: PullMode = PullMode.NONE,
                  initial: Optional[bool] = None) -> bool:
        """
        Setup GPIO pin.
        
        Args:
            pin: GPIO pin number (BCM)
            mode: Pin mode
            pull: Pull resistor mode
            initial: Initial state for output pins
            
        Returns:
            True if successful
        """
        if not self.initialized:
            return False
        
        try:
            if mode == PinMode.INPUT:
                pull_mode = GPIO.PUD_OFF
                
                if pull == PullMode.UP:
                    pull_mode = GPIO.PUD_UP
                elif pull == PullMode.DOWN:
                    pull_mode = GPIO.PUD_DOWN
                
                GPIO.setup(pin, GPIO.IN, pull_up_down=pull_mode)
                
            elif mode == PinMode.OUTPUT:
                initial_state = GPIO.LOW if initial is None else (GPIO.HIGH if initial else GPIO.LOW)
                GPIO.setup(pin, GPIO.OUT, initial=initial_state)
            
            self.pins_configured[pin] = mode
            
            self.logger.debug(f"Pin {pin} configured as {mode.value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pin setup failed: {e}")
            return False
    
    def digital_write(self, pin: int, state: bool) -> bool:
        """
        Write digital value to pin.
        
        Args:
            pin: GPIO pin number
            state: Output state (True=HIGH, False=LOW)
            
        Returns:
            True if successful
        """
        if not self.initialized:
            return False
        
        if pin not in self.pins_configured:
            self.logger.error(f"Pin {pin} not configured")
            return False
        
        try:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            return True
            
        except Exception as e:
            self.logger.error(f"Digital write failed: {e}")
            return False
    
    def digital_read(self, pin: int) -> Optional[bool]:
        """
        Read digital value from pin.
        
        Args:
            pin: GPIO pin number
            
        Returns:
            Pin state or None
        """
        if not self.initialized:
            return None
        
        if pin not in self.pins_configured:
            self.logger.error(f"Pin {pin} not configured")
            return None
        
        try:
            state = GPIO.input(pin)
            return state == GPIO.HIGH
            
        except Exception as e:
            self.logger.error(f"Digital read failed: {e}")
            return None
    
    def setup_pwm(self, pin: int, frequency: float) -> bool:
        """
        Setup PWM on pin.
        
        Args:
            pin: GPIO pin number
            frequency: PWM frequency in Hz
            
        Returns:
            True if successful
        """
        if not self.initialized:
            return False
        
        try:
            if pin not in self.pins_configured:
                self.setup_pin(pin, PinMode.OUTPUT)
            
            pwm = GPIO.PWM(pin, frequency)
            pwm.start(0)
            
            self.pwm_instances[pin] = pwm
            self.pins_configured[pin] = PinMode.PWM
            
            self.logger.debug(f"PWM setup on pin {pin} at {frequency} Hz")
            
            return True
            
        except Exception as e:
            self.logger.error(f"PWM setup failed: {e}")
            return False
    
    def set_pwm_duty_cycle(self, pin: int, duty_cycle: float) -> bool:
        """
        Set PWM duty cycle.
        
        Args:
            pin: GPIO pin number
            duty_cycle: Duty cycle (0-100%)
            
        Returns:
            True if successful
        """
        if pin not in self.pwm_instances:
            self.logger.error(f"PWM not setup on pin {pin}")
            return False
        
        try:
            duty_cycle = max(0.0, min(100.0, duty_cycle))
            
            self.pwm_instances[pin].ChangeDutyCycle(duty_cycle)
            
            return True
            
        except Exception as e:
            self.logger.error(f"PWM duty cycle change failed: {e}")
            return False
    
    def stop_pwm(self, pin: int) -> bool:
        """
        Stop PWM on pin.
        
        Args:
            pin: GPIO pin number
            
        Returns:
            True if successful
        """
        if pin not in self.pwm_instances:
            return False
        
        try:
            self.pwm_instances[pin].stop()
            del self.pwm_instances[pin]
            
            return True
            
        except Exception as e:
            self.logger.error(f"PWM stop failed: {e}")
            return False
    
    def add_event_detect(self, pin: int, callback: Callable,
                        edge: str = 'both', bouncetime: int = 200) -> bool:
        """
        Add interrupt callback.
        
        Args:
            pin: GPIO pin number
            callback: Callback function
            edge: Edge type ('rising', 'falling', 'both')
            bouncetime: Debounce time in ms
            
        Returns:
            True if successful
        """
        if not self.initialized:
            return False
        
        try:
            edge_map = {
                'rising': GPIO.RISING,
                'falling': GPIO.FALLING,
                'both': GPIO.BOTH
            }
            
            edge_type = edge_map.get(edge, GPIO.BOTH)
            
            GPIO.add_event_detect(pin, edge_type, 
                                callback=callback,
                                bouncetime=bouncetime)
            
            self.logger.debug(f"Event detect added on pin {pin}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Event detect failed: {e}")
            return False
    
    def remove_event_detect(self, pin: int) -> bool:
        """
        Remove interrupt callback.
        
        Args:
            pin: GPIO pin number
            
        Returns:
            True if successful
        """
        if not self.initialized:
            return False
        
        try:
            GPIO.remove_event_detect(pin)
            return True
            
        except Exception as e:
            self.logger.error(f"Remove event detect failed: {e}")
            return False
    
    def cleanup(self, pin: Optional[int] = None):
        """
        Cleanup GPIO.
        
        Args:
            pin: Specific pin to cleanup, or None for all
        """
        if not self.initialized:
            return
        
        try:
            # Stop all PWM
            for pwm_pin in list(self.pwm_instances.keys()):
                self.stop_pwm(pwm_pin)
            
            # Cleanup GPIO
            if pin is not None:
                GPIO.cleanup(pin)
                if pin in self.pins_configured:
                    del self.pins_configured[pin]
            else:
                GPIO.cleanup()
                self.pins_configured.clear()
            
            self.logger.info("GPIO cleanup complete")
            
        except Exception as e:
            self.logger.error(f"GPIO cleanup failed: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    gpio = GPIOHandler()
    
    # Test output
    gpio.setup_pin(17, PinMode.OUTPUT)
    gpio.digital_write(17, True)
    
    print("GPIO handler initialized")
