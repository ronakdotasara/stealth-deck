"""
================================================================================
state_manager.py - State Management for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Centralized state management for Stealth Deck system.
Tracks system mode, device status, and application state.

Features:
- Thread-safe state access
- State change notifications
- State history tracking
- Persistence to disk
- State validation

================================================================================
"""

import logging
import threading
import time
import json
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path
from enum import IntEnum


class SystemMode(IntEnum):
    """System operation modes."""
    CALCULATOR = 0
    SMART = 1
    P2P = 2
    WIFI_SNIFFER = 3
    CLIPBOARD = 4
    NOTES = 5
    SETTINGS = 6
    PANIC = 7


class StateManager:
    """
    Centralized state manager for Stealth Deck.
    
    Manages system mode, device status, and application state.
    """
    
    def __init__(self):
        """Initialize state manager."""
        self.logger = logging.getLogger('state_manager')
        
        self.lock = threading.Lock()
        
        self.current_mode = SystemMode.CALCULATOR
        self.previous_mode = SystemMode.CALCULATOR
        
        self.device_unlocked = False
        
        self.state_data: Dict[str, Any] = {
            'mode': SystemMode.CALCULATOR,
            'unlocked': False,
            'uptime': 0.0,
            'last_activity': time.time()
        }
        
        self.state_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
        self.callbacks: Dict[str, List[Callable]] = {
            'mode_change': [],
            'unlock': [],
            'lock': [],
            'panic': []
        }
        
        self.state_file = Path("/var/lib/stealth-deck/state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.start_time = time.time()
        
        self.load_state()
    
    def get_mode(self) -> SystemMode:
        """
        Get current system mode.
        
        Returns:
            Current mode
        """
        with self.lock:
            return self.current_mode
    
    def set_mode(self, mode: SystemMode) -> bool:
        """
        Set system mode.
        
        Args:
            mode: New mode
            
        Returns:
            True if mode changed
        """
        with self.lock:
            if self.current_mode == mode:
                return False
            
            self.logger.info(f"Mode change: {self.current_mode.name} -> {mode.name}")
            
            self.previous_mode = self.current_mode
            self.current_mode = mode
            
            self.state_data['mode'] = mode
            self._update_activity()
            self._add_to_history('mode_change', {
                'from': self.previous_mode.name,
                'to': mode.name
            })
            
            self._trigger_callbacks('mode_change', mode)
            
            self.save_state()
            
            return True
    
    def get_previous_mode(self) -> SystemMode:
        """
        Get previous system mode.
        
        Returns:
            Previous mode
        """
        with self.lock:
            return self.previous_mode
    
    def is_unlocked(self) -> bool:
        """
        Check if device is unlocked.
        
        Returns:
            True if unlocked
        """
        with self.lock:
            return self.device_unlocked
    
    def unlock(self) -> None:
        """Unlock device."""
        with self.lock:
            if not self.device_unlocked:
                self.logger.info("Device unlocked")
                self.device_unlocked = True
                self.state_data['unlocked'] = True
                self._update_activity()
                self._add_to_history('unlock', {})
                self._trigger_callbacks('unlock', True)
                self.save_state()
    
    def lock(self) -> None:
        """Lock device."""
        with self.lock:
            if self.device_unlocked:
                self.logger.info("Device locked")
                self.device_unlocked = False
                self.state_data['unlocked'] = False
                self._update_activity()
                self._add_to_history('lock', {})
                self._trigger_callbacks('lock', False)
                self.save_state()
    
    def panic(self) -> None:
        """Activate panic mode."""
        with self.lock:
            self.logger.warning("PANIC MODE ACTIVATED")
            
            self.device_unlocked = False
            self.current_mode = SystemMode.PANIC
            self.state_data['unlocked'] = False
            self.state_data['mode'] = SystemMode.PANIC
            
            self._add_to_history('panic', {})
            self._trigger_callbacks('panic', True)
            
            self.save_state()
    
    def get_uptime(self) -> float:
        """
        Get system uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        return time.time() - self.start_time
    
    def get_last_activity(self) -> float:
        """
        Get time of last activity.
        
        Returns:
            Timestamp of last activity
        """
        with self.lock:
            return self.state_data['last_activity']
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        with self.lock:
            self._update_activity()
    
    def _update_activity(self) -> None:
        """Update activity timestamp (internal, no lock)."""
        self.state_data['last_activity'] = time.time()
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get complete state data.
        
        Returns:
            State dictionary
        """
        with self.lock:
            state = self.state_data.copy()
            state['mode'] = self.current_mode.name
            state['uptime'] = self.get_uptime()
            return state
    
    def set_state_value(self, key: str, value: Any) -> None:
        """
        Set custom state value.
        
        Args:
            key: State key
            value: State value
        """
        with self.lock:
            self.state_data[key] = value
            self._update_activity()
            self.logger.debug(f"State updated: {key} = {value}")
    
    def get_state_value(self, key: str, default: Any = None) -> Any:
        """
        Get custom state value.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        with self.lock:
            return self.state_data.get(key, default)
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Register callback for state change event.
        
        Args:
            event: Event name (mode_change, unlock, lock, panic)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        
        self.callbacks[event].append(callback)
        self.logger.debug(f"Callback registered for: {event}")
    
    def _trigger_callbacks(self, event: str, data: Any) -> None:
        """
        Trigger callbacks for event.
        
        Args:
            event: Event name
            data: Event data
        """
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Callback error for {event}: {e}")
    
    def _add_to_history(self, event: str, data: Dict[str, Any]) -> None:
        """
        Add event to state history.
        
        Args:
            event: Event type
            data: Event data
        """
        history_entry = {
            'timestamp': time.time(),
            'event': event,
            'data': data
        }
        
        self.state_history.append(history_entry)
        
        if len(self.state_history) > self.max_history_size:
            self.state_history.pop(0)
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get state change history.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        with self.lock:
            return self.state_history[-limit:]
    
    def save_state(self) -> bool:
        """
        Save state to disk.
        
        Returns:
            True if saved successfully
        """
        try:
            state_to_save = {
                'mode': self.current_mode.name,
                'unlocked': self.device_unlocked,
                'timestamp': time.time(),
                'data': self.state_data
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_to_save, f, indent=2)
            
            self.logger.debug(f"State saved to {self.state_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            return False
    
    def load_state(self) -> bool:
        """
        Load state from disk.
        
        Returns:
            True if loaded successfully
        """
        try:
            if not self.state_file.exists():
                self.logger.info("No saved state found, using defaults")
                return False
            
            with open(self.state_file, 'r') as f:
                saved_state = json.load(f)
            
            if 'mode' in saved_state:
                try:
                    mode = SystemMode[saved_state['mode']]
                    self.current_mode = mode
                except KeyError:
                    self.logger.warning(f"Invalid mode in saved state: {saved_state['mode']}")
            
            if 'data' in saved_state:
                self.state_data.update(saved_state['data'])
            
            self.logger.info(f"State loaded from {self.state_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            return False
    
    def clear_state(self) -> None:
        """Clear state and reset to defaults."""
        with self.lock:
            self.logger.info("Clearing state")
            
            self.current_mode = SystemMode.CALCULATOR
            self.previous_mode = SystemMode.CALCULATOR
            self.device_unlocked = False
            
            self.state_data = {
                'mode': SystemMode.CALCULATOR,
                'unlocked': False,
                'uptime': 0.0,
                'last_activity': time.time()
            }
            
            self.state_history.clear()
            
            self.save_state()
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get state manager info.
        
        Returns:
            Info dictionary
        """
        with self.lock:
            return {
                'current_mode': self.current_mode.name,
                'previous_mode': self.previous_mode.name,
                'unlocked': self.device_unlocked,
                'uptime': self.get_uptime(),
                'history_size': len(self.state_history),
                'callbacks_registered': sum(len(v) for v in self.callbacks.values())
            }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    state = StateManager()
    
    print(f"Initial mode: {state.get_mode().name}")
    
    state.unlock()
    state.set_mode(SystemMode.SMART)
    
    print(f"Current mode: {state.get_mode().name}")
    print(f"Unlocked: {state.is_unlocked()}")
    print(f"Uptime: {state.get_uptime():.2f}s")
    
    state.panic()
    
    print(f"After panic: {state.get_mode().name}")

