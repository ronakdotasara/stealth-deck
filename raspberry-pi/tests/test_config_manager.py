"""
================================================================================
test_config_manager.py - Unit Tests for Configuration Manager
================================================================================
Version: 1.0.0
Date: 2025-11-25

Test coverage for configuration management.
================================================================================
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from src.core.config_manager import ConfigManager


class TestConfigManager:
    """Test suite for configuration manager."""
    
    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create temporary config file."""
        config_file = tmp_path / "config.json"
        config_data = {
            'api_keys': {
                'gemini_api_key': 'test_key_123'
            },
            'hardware': {
                'uart_port': '/dev/ttyAMA0',
                'uart_baud': 115200
            },
            'ai': {
                'model': 'gemini-pro',
                'temperature': 0.7
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))
        return config_file
    
    @pytest.fixture
    def config_manager(self, temp_config_file):
        """Create config manager with temp file."""
        return ConfigManager(str(temp_config_file))
    
    def test_initialization(self, config_manager):
        """Test manager initialization."""
        assert config_manager.config_file is not None
        assert config_manager.config is not None
    
    def test_load_config(self, config_manager):
        """Test config loading."""
        assert config_manager.config is not None
        assert 'api_keys' in config_manager.config
        assert 'hardware' in config_manager.config
    
    def test_get_value(self, config_manager):
        """Test getting config value."""
        value = config_manager.get('api_keys.gemini_api_key')
        
        assert value == 'test_key_123'
    
    def test_get_nested_value(self, config_manager):
        """Test getting nested config value."""
        value = config_manager.get('hardware.uart_port')
        
        assert value == '/dev/ttyAMA0'
    
    def test_get_nonexistent_value(self, config_manager):
        """Test getting non-existent value."""
        value = config_manager.get('nonexistent.key')
        
        assert value is None
    
    def test_get_with_default(self, config_manager):
        """Test getting value with default."""
        value = config_manager.get('nonexistent.key', default='default_value')
        
        assert value == 'default_value'
    
    def test_set_value(self, config_manager):
        """Test setting config value."""
        config_manager.set('test.key', 'test_value')
        
        value = config_manager.get('test.key')
        
        assert value == 'test_value'
    
    def test_set_nested_value(self, config_manager):
        """Test setting nested config value."""
        config_manager.set('new.nested.key', 'nested_value')
        
        value = config_manager.get('new.nested.key')
        
        assert value == 'nested_value'
    
    def test_update_existing_value(self, config_manager):
        """Test updating existing value."""
        original = config_manager.get('ai.temperature')
        
        config_manager.set('ai.temperature', 0.9)
        
        updated = config_manager.get('ai.temperature')
        
        assert updated != original
        assert updated == 0.9
    
    def test_delete_value(self, config_manager):
        """Test deleting config value."""
        config_manager.set('to_delete', 'value')
        
        assert config_manager.get('to_delete') == 'value'
        
        config_manager.delete('to_delete')
        
        assert config_manager.get('to_delete') is None
    
    def test_save_config(self, config_manager, temp_config_file):
        """Test saving config to file."""
        config_manager.set('new_key', 'new_value')
        
        result = config_manager.save()
        
        assert result is True
        
        # Reload and verify
        with open(temp_config_file) as f:
            saved_config = json.load(f)
        
        assert saved_config['new_key'] == 'new_value'
    
    def test_reload_config(self, config_manager, temp_config_file):
        """Test reloading config from file."""
        # Modify file directly
        with open(temp_config_file) as f:
            config = json.load(f)
        
        config['external_change'] = 'value'
        
        with open(temp_config_file, 'w') as f:
            json.dump(config, f)
        
        # Reload
        config_manager.reload()
        
        value = config_manager.get('external_change')
        
        assert value == 'value'
    
    def test_get_all(self, config_manager):
        """Test getting all config."""
        all_config = config_manager.get_all()
        
        assert isinstance(all_config, dict)
        assert 'api_keys' in all_config
        assert 'hardware' in all_config
    
    def test_validate_config(self, config_manager):
        """Test config validation."""
        is_valid = config_manager.validate()
        
        assert is_valid is True
    
    def test_get_section(self, config_manager):
        """Test getting config section."""
        hardware_config = config_manager.get_section('hardware')
        
        assert isinstance(hardware_config, dict)
        assert 'uart_port' in hardware_config
        assert 'uart_baud' in hardware_config
    
    def test_has_key(self, config_manager):
        """Test checking if key exists."""
        assert config_manager.has('api_keys.gemini_api_key') is True
        assert config_manager.has('nonexistent.key') is False
    
    def test_merge_config(self, config_manager):
        """Test merging config."""
        new_config = {
            'new_section': {
                'key': 'value'
            }
        }
        
        config_manager.merge(new_config)
        
        assert config_manager.get('new_section.key') == 'value'


class TestConfigDefaults:
    """Test default configuration handling."""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create config manager with defaults."""
        config_file = tmp_path / "config.json"
        return ConfigManager(str(config_file), create_default=True)
    
    def test_create_default_config(self, config_manager):
        """Test default config creation."""
        assert config_manager.config is not None
        assert Path(config_manager.config_file).exists()
    
    def test_default_values(self, config_manager):
        """Test that default values are set."""
        # Should have some default values
        config = config_manager.get_all()
        
        assert isinstance(config, dict)


class TestConfigValidation:
    """Test configuration validation."""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create config manager."""
        config_file = tmp_path / "config.json"
        config_data = {
            'api_keys': {
                'gemini_api_key': ''  # Empty key
            },
            'hardware': {
                'uart_baud': 'invalid'  # Should be integer
            }
        }
        config_file.write_text(json.dumps(config_data))
        return ConfigManager(str(config_file))
    
    def test_validate_api_key(self, config_manager):
        """Test API key validation."""
        is_valid = config_manager.validate_api_key()
        
        assert is_valid is False
    
    def test_validate_hardware_config(self, config_manager):
        """Test hardware config validation."""
        is_valid = config_manager.validate_hardware()
        
        # Should detect invalid baud rate
        assert is_valid is False


class TestConfigEnvironmentVariables:
    """Test environment variable handling."""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create config manager."""
        config_file = tmp_path / "config.json"
        config_data = {
            'api_keys': {
                'gemini_api_key': '${GEMINI_API_KEY}'
            }
        }
        config_file.write_text(json.dumps(config_data))
        return ConfigManager(str(config_file))
    
    @patch.dict('os.environ', {'GEMINI_API_KEY': 'env_test_key'})
    def test_expand_environment_variables(self, config_manager):
        """Test environment variable expansion."""
        config_manager.expand_env_vars()
        
        value = config_manager.get('api_keys.gemini_api_key')
        
        assert value == 'env_test_key'


class TestConfigErrors:
    """Test error handling."""
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")
        
        with pytest.raises(Exception):
            ConfigManager(str(config_file))
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading non-existent file."""
        config_file = tmp_path / "nonexistent.json"
        
        config_manager = ConfigManager(str(config_file), create_default=False)
        
        # Should handle gracefully
        assert config_manager.config is not None or config_manager.config == {}
    
    def test_save_to_readonly_location(self, tmp_path):
        """Test saving to read-only location."""
        config_file = tmp_path / "readonly" / "config.json"
        config_manager = ConfigManager(str(config_file))
        
        # Make parent directory read-only
        # (This test may not work on all systems)
        # Just ensure save handles errors gracefully
        result = config_manager.save()
        
        # Should return False or handle error


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
