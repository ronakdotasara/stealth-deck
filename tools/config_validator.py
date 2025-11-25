#!/usr/bin/env python3
"""
================================================================================
config_validator.py - Configuration Validator
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Validates Stealth Deck configuration files.
Checks for correctness, completeness, and security.

Features:
- Schema validation
- Value range checking
- Security validation
- Dependency checking
- Suggestions

================================================================================
"""

import json
import sys
from typing import Dict, List, Any
from pathlib import Path


class ConfigValidator:
    """
    Configuration validator.
    
    Validates configuration files against schema.
    """
    
    def __init__(self):
        """Initialize validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        
        self.schema = self.get_schema()
    
    def get_schema(self) -> Dict:
        """Get configuration schema."""
        return {
            'api_keys': {
                'required': False,
                'type': dict,
                'fields': {
                    'gemini_api_key': {'type': str, 'required': True, 'min_length': 20}
                }
            },
            'hardware': {
                'required': True,
                'type': dict,
                'fields': {
                    'uart_port': {'type': str, 'required': True},
                    'uart_baud': {'type': int, 'required': True, 'values': [9600, 19200, 38400, 57600, 115200]},
                    'camera_enabled': {'type': bool, 'required': True},
                    'camera_resolution': {'type': list, 'required': False},
                    'display_width': {'type': int, 'required': True, 'min': 1, 'max': 4096},
                    'display_height': {'type': int, 'required': True, 'min': 1, 'max': 4096}
                }
            },
            'ai': {
                'required': True,
                'type': dict,
                'fields': {
                    'model': {'type': str, 'required': True},
                    'vision_model': {'type': str, 'required': False},
                    'temperature': {'type': float, 'required': True, 'min': 0.0, 'max': 1.0},
                    'max_tokens': {'type': int, 'required': True, 'min': 1, 'max': 8192},
                    'cache_responses': {'type': bool, 'required': False}
                }
            },
            'security': {
                'required': True,
                'type': dict,
                'fields': {
                    'encryption_enabled': {'type': bool, 'required': True},
                    'wipe_on_panic': {'type': bool, 'required': False},
                    'unlock_code_hash': {'type': str, 'required': True, 'min_length': 32}
                }
            },
            'storage': {
                'required': False,
                'type': dict,
                'fields': {
                    'max_cache_size_mb': {'type': int, 'required': False, 'min': 10, 'max': 1000},
                    'auto_cleanup': {'type': bool, 'required': False},
                    'cleanup_days': {'type': int, 'required': False, 'min': 1, 'max': 365}
                }
            },
            'power': {
                'required': False,
                'type': dict,
                'fields': {
                    'cpu_mode': {'type': str, 'required': False, 'values': ['powersave', 'balanced', 'performance']},
                    'auto_sleep': {'type': bool, 'required': False},
                    'sleep_timeout': {'type': int, 'required': False, 'min': 30, 'max': 3600}
                }
            }
        }
    
    def validate(self, config: Dict) -> bool:
        """
        Validate configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if valid
        """
        self.errors.clear()
        self.warnings.clear()
        self.suggestions.clear()
        
        # Check top-level sections
        for section, schema in self.schema.items():
            if schema['required'] and section not in config:
                self.errors.append(f"Missing required section: {section}")
                continue
            
            if section in config:
                self.validate_section(section, config[section], schema)
        
        # Additional validations
        self.validate_security(config)
        self.validate_dependencies(config)
        self.generate_suggestions(config)
        
        return len(self.errors) == 0
    
    def validate_section(self, section_name: str, section_data: Any, schema: Dict):
        """Validate configuration section."""
        if not isinstance(section_data, schema['type']):
            self.errors.append(f"{section_name}: Expected {schema['type'].__name__}, got {type(section_data).__name__}")
            return
        
        if 'fields' not in schema:
            return
        
        # Check fields
        for field, field_schema in schema['fields'].items():
            if field_schema.get('required', False) and field not in section_data:
                self.errors.append(f"{section_name}.{field}: Required field missing")
                continue
            
            if field in section_data:
                self.validate_field(f"{section_name}.{field}", section_data[field], field_schema)
    
    def validate_field(self, field_path: str, value: Any, schema: Dict):
        """Validate field value."""
        # Type check
        expected_type = schema['type']
        if not isinstance(value, expected_type):
            self.errors.append(f"{field_path}: Expected {expected_type.__name__}, got {type(value).__name__}")
            return
        
        # String validations
        if expected_type == str:
            if 'min_length' in schema and len(value) < schema['min_length']:
                self.errors.append(f"{field_path}: String too short (min {schema['min_length']})")
            
            if 'max_length' in schema and len(value) > schema['max_length']:
                self.errors.append(f"{field_path}: String too long (max {schema['max_length']})")
        
        # Numeric validations
        if expected_type in [int, float]:
            if 'min' in schema and value < schema['min']:
                self.errors.append(f"{field_path}: Value too small (min {schema['min']})")
            
            if 'max' in schema and value > schema['max']:
                self.errors.append(f"{field_path}: Value too large (max {schema['max']})")
        
        # Enum validations
        if 'values' in schema and value not in schema['values']:
            self.errors.append(f"{field_path}: Invalid value. Must be one of {schema['values']}")
    
    def validate_security(self, config: Dict):
        """Validate security settings."""
        if 'security' not in config:
            return
        
        security = config['security']
        
        # Check encryption
        if not security.get('encryption_enabled', False):
            self.warnings.append("Encryption is disabled - data will not be protected")
        
        # Check unlock code
        if 'unlock_code_hash' in security:
            if len(security['unlock_code_hash']) < 32:
                self.errors.append("unlock_code_hash too short")
        
        # API key security
        if 'api_keys' in config and 'gemini_api_key' in config['api_keys']:
            key = config['api_keys']['gemini_api_key']
            if key == 'your-api-key-here' or key == '':
                self.warnings.append("Default or empty API key detected")
    
    def validate_dependencies(self, config: Dict):
        """Validate configuration dependencies."""
        # Camera enabled but no vision model
        if config.get('hardware', {}).get('camera_enabled', False):
            if not config.get('ai', {}).get('vision_model'):
                self.warnings.append("Camera enabled but no vision model configured")
        
        # Auto cleanup enabled but no cleanup days
        if config.get('storage', {}).get('auto_cleanup', False):
            if 'cleanup_days' not in config.get('storage', {}):
                self.warnings.append("Auto cleanup enabled but cleanup_days not set")
        
        # Auto sleep enabled but no timeout
        if config.get('power', {}).get('auto_sleep', False):
            if 'sleep_timeout' not in config.get('power', {}):
                self.warnings.append("Auto sleep enabled but sleep_timeout not set")
    
    def generate_suggestions(self, config: Dict):
        """Generate configuration suggestions."""
        # Performance suggestions
        if config.get('ai', {}).get('max_tokens', 0) > 2048:
            self.suggestions.append("Large max_tokens may slow down responses")
        
        # Storage suggestions
        cache_size = config.get('storage', {}).get('max_cache_size_mb', 0)
        if cache_size > 500:
            self.suggestions.append("Large cache size may use significant storage")
        
        # Power suggestions
        if config.get('power', {}).get('cpu_mode') == 'performance':
            self.suggestions.append("Performance mode uses more power - consider 'balanced'")
    
    def print_results(self):
        """Print validation results."""
        print("\n" + "=" * 80)
        print("Configuration Validation Results")
        print("=" * 80)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.suggestions:
            print(f"\n💡 SUGGESTIONS ({len(self.suggestions)}):")
            for suggestion in self.suggestions:
                print(f"  - {suggestion}")
        
        if not self.errors and not self.warnings:
            print("\n✅ Configuration is valid!")
        
        print("=" * 80 + "\n")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: config_validator.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    # Load configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)
    
    # Validate
    validator = ConfigValidator()
    is_valid = validator.validate(config)
    
    # Print results
    validator.print_results()
    
    # Exit code
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
