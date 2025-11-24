
================================================================================
"""

import json
import os
import logging
import threading
from typing import Any, Dict, Optional, List
from pathlib import Path


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


class ConfigManager:
    """
    Configuration manager for Stealth Deck.
    
    Handles loading, validation, and access to configuration settings.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration JSON file
            
        Raises:
            ConfigurationError: If configuration file cannot be loaded
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger('config_manager')
        
        self.load()
    
    def load(self) -> None:
        """
        Load configuration from file.
        
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        try:
            self.logger.info(f"Loading configuration from: {self.config_path}")
            
            if not os.path.exists(self.config_path):
                raise ConfigurationError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            with self.lock:
                self.config = config_data
            
            self._validate_config()
            self._apply_environment_variables()
            
            self.logger.info("Configuration loaded successfully")
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def reload(self) -> None:
        """
        Reload configuration from file.
        
        Useful for hot-reloading configuration changes.
        """
        self.logger.info("Reloading configuration...")
        self.load()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Supports dot notation for nested keys (e.g., 'hardware.uart_port').
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        with self.lock:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by key.
        
        Supports dot notation for nested keys.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        with self.lock:
            keys = key.split('.')
            config = self.config
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
        
        self.logger.debug(f"Configuration updated: {key} = {value}")
    
    def has(self, key: str) -> bool:
        """
        Check if configuration key exists.
        
        Args:
            key: Configuration key (supports dot notation)
            
        Returns:
            True if key exists, False otherwise
        """
        with self.lock:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return False
            
            return True
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (supports dot notation)
            
        Returns:
            Section dictionary or empty dict if not found
        """
        value = self.get(section, {})
        
        if not isinstance(value, dict):
            return {}
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration.
        
        Returns:
            Complete configuration dictionary
        """
        with self.lock:
            return self.config.copy()
    
    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            path: Path to save to (default: original config_path)
        """
        save_path = path or self.config_path
        
        try:
            self.logger.info(f"Saving configuration to: {save_path}")
            
            with self.lock:
                config_data = self.config.copy()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def _validate_config(self) -> None:
        """
        Validate configuration structure.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        required_sections = [
            'api_keys',
            'hardware',
            'features',
            'security',
            'power'
        ]
        
        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Missing required section: {section}")
        
        required_keys = [
            'api_keys.gemini_api_key',
            'hardware.uart_port',
            'hardware.uart_baud',
            'hardware.camera_resolution',
            'features.enable_p2p',
            'features.enable_search',
            'security.panic_key_combo',
            'security.unlock_sequence',
            'power.idle_timeout_seconds'
        ]
        
        for key in required_keys:
            if not self.has(key):
                raise ConfigurationError(f"Missing required configuration key: {key}")
        
        if not isinstance(self.get('hardware.camera_resolution'), list):
            raise ConfigurationError("hardware.camera_resolution must be a list")
        
        if len(self.get('hardware.camera_resolution')) != 2:
            raise ConfigurationError("hardware.camera_resolution must have exactly 2 values")
        
        self.logger.debug("Configuration validation passed")
    
    def _apply_environment_variables(self) -> None:
        """
        Apply environment variable overrides.
        
        Looks for environment variables in the format:
        STEALTH_DECK_<SECTION>_<KEY>
        
        Example: STEALTH_DECK_API_KEYS_GEMINI_API_KEY
        """
        env_prefix = 'STEALTH_DECK_'
        
        for env_var, env_value in os.environ.items():
            if not env_var.startswith(env_prefix):
                continue
            
            config_key = env_var[len(env_prefix):].lower().replace('_', '.')
            
            try:
                value = json.loads(env_value)
            except json.JSONDecodeError:
                value = env_value
            
            self.set(config_key, value)
            self.logger.debug(f"Applied environment variable: {env_var}")
    
    def validate_api_key(self, key_name: str) -> bool:
        """
        Validate that API key is configured.
        
        Args:
            key_name: Name of API key (e.g., 'gemini_api_key')
            
        Returns:
            True if valid, False otherwise
        """
        api_key = self.get(f'api_keys.{key_name}')
        
        if not api_key:
            return False
        
        if api_key.startswith('YOUR_'):
            return False
        
        if len(api_key) < 10:
            return False
        
        return True
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """
        Get hardware configuration section.
        
        Returns:
            Hardware configuration dictionary
        """
        return self.get_section('hardware')
    
    def get_features_config(self) -> Dict[str, Any]:
        """
        Get features configuration section.
        
        Returns:
            Features configuration dictionary
        """
        return self.get_section('features')
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        Get security configuration section.
        
        Returns:
            Security configuration dictionary
        """
        return self.get_section('security')
    
    def get_power_config(self) -> Dict[str, Any]:
        """
        Get power management configuration section.
        
        Returns:
            Power configuration dictionary
        """
        return self.get_section('power')
    
    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature: Feature name (e.g., 'p2p', 'search')
            
        Returns:
            True if enabled, False otherwise
        """
        return self.get(f'features.enable_{feature}', False)
    
    def get_display_config(self) -> Dict[str, Any]:
        """
        Get display configuration.
        
        Returns:
            Display configuration dictionary
        """
        return {
            'width': 240,
            'height': 536,
            'brightness_stealth': self.get('power.display_brightness_stealth', 5),
            'brightness_normal': self.get('power.display_brightness_normal', 30),
            'brightness_outdoor': 100
        }
    
    def get_uart_config(self) -> Dict[str, Any]:
        """
        Get UART configuration.
        
        Returns:
            UART configuration dictionary
        """
        return {
            'port': self.get('hardware.uart_port', '/dev/serial0'),
            'baud': self.get('hardware.uart_baud', 115200),
            'timeout': 0.1
        }
    
    def get_camera_config(self) -> Dict[str, Any]:
        """
        Get camera configuration.
        
        Returns:
            Camera configuration dictionary
        """
        resolution = self.get('hardware.camera_resolution', [1640, 1232])
        
        return {
            'resolution': tuple(resolution),
            'format': 'RGB888',
            'rotation': 0,
            'quality': 85
        }
    
    def get_bluetooth_config(self) -> Dict[str, Any]:
        """
        Get Bluetooth configuration.
        
        Returns:
            Bluetooth configuration dictionary
        """
        return {
            'device_name': 'StealthDeck',
            'discoverable': False,
            'pairable': True,
            'timeout': 30
        }
    
    def dump_config(self) -> str:
        """
        Dump configuration as formatted JSON string.
        
        Returns:
            JSON string
        """
        with self.lock:
            return json.dumps(self.config, indent=2)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ConfigManager(path='{self.config_path}')"
    
    def __str__(self) -> str:
        """String representation."""
        return f"ConfigManager with {len(self.config)} sections"


def create_default_config(path: str) -> None:
    """
    Create default configuration file.
    
    Args:
        path: Path where to create config file
    """
    default_config = {
        "api_keys": {
            "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE"
        },
        "hardware": {
            "uart_port": "/dev/serial0",
            "uart_baud": 115200,
            "camera_resolution": [1640, 1232]
        },
        "features": {
            "enable_p2p": True,
            "enable_wifi_sniffer": True,
            "enable_search": True
        },
        "security": {
            "panic_key_combo": "FN+FIX",
            "unlock_sequence": "FN+5+5+5",
            "encryption_enabled": True
        },
        "power": {
            "idle_timeout_seconds": 30,
            "display_brightness_stealth": 5,
            "display_brightness_normal": 30
        }
    }
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Default configuration created at: {path}")


if __name__ == '__main__':
    create_default_config('/tmp/stealth-deck-config.json')
    
    config = ConfigManager('/tmp/stealth-deck-config.json')
    print(config.dump_config())

