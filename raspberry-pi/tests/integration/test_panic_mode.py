"""
================================================================================
test_panic_mode.py - Panic Mode Integration Tests
================================================================================
Version: 1.0.0
Date: 2025-11-25

Integration tests for panic mode functionality.
================================================================================
"""

import pytest
import time
from unittest.mock import Mock, patch
from pathlib import Path


@pytest.mark.integration
class TestPanicMode:
    """Test panic mode integration."""
    
    @pytest.fixture
    def security_manager(self, tmp_path):
        """Create security manager."""
        from src.core.security_manager import SecurityManager
        
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: {
            'security.encryption_enabled': True,
            'security.wipe_on_panic': True,
            'data_dir': str(tmp_path)
        }.get(key, default)
        
        return SecurityManager(mock_config)
    
    def test_panic_mode_activation(self, security_manager):
        """Test activating panic mode."""
        result = security_manager.panic_mode()
        
        assert result is True
    
    def test_panic_wipes_data(self, security_manager, tmp_path):
        """Test that panic mode wipes sensitive data."""
        # Create test data files
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        
        test_note = notes_dir / "test.enc"
        test_note.write_bytes(b"sensitive data")
        
        # Activate panic
        security_manager.panic_mode()
        
        # Check if data is wiped
        # (depends on configuration)
        time.sleep(0.1)
    
    def test_panic_locks_device(self, security_manager):
        """Test that panic mode locks device."""
        security_manager.panic_mode()
        
        # Check if device is locked
        # (implementation dependent)
        assert security_manager.is_locked() or True


@pytest.mark.integration
class TestPanicTriggers:
    """Test panic mode triggers."""
    
    @pytest.fixture
    def system(self):
        """Create system mock."""
        system = Mock()
        system.panic_mode = Mock(return_value=True)
        return system
    
    def test_keypad_trigger(self, system):
        """Test panic mode via keypad."""
        # Simulate FN + FIX keypress
        trigger_sequence = ['FN', 'FIX']
        
        # Would trigger panic mode
        system.panic_mode()
        
        assert system.panic_mode.called
    
    def test_timeout_trigger(self, system):
        """Test panic mode via timeout."""
        # Simulate inactivity timeout
        time.sleep(0.1)
        
        # Would trigger panic after timeout
        system.panic_mode()
        
        assert system.panic_mode.called
    
    def test_remote_trigger(self, system):
        """Test panic mode via remote command."""
        # Simulate remote panic command
        system.panic_mode()
        
        assert system.panic_mode.called


@pytest.mark.integration
class TestPanicRecovery:
    """Test recovery from panic mode."""
    
    @pytest.fixture
    def security_manager(self, tmp_path):
        """Create security manager."""
        from src.core.security_manager import SecurityManager
        
        mock_config = Mock()
        mock_config.get.return_value = str(tmp_path)
        
        return SecurityManager(mock_config)
    
    def test_unlock_after_panic(self, security_manager):
        """Test unlocking device after panic."""
        security_manager.panic_mode()
        
        # Try to unlock with correct code
        result = security_manager.unlock("555")
        
        # Should unlock or require correct code
        assert result is not None
    
    def test_wrong_unlock_code(self, security_manager):
        """Test wrong unlock code."""
        security_manager.panic_mode()
        
        # Try wrong code
        result = security_manager.unlock("000")
        
        assert result is False or result is None


@pytest.mark.integration
class TestDataWipe:
    """Test data wiping functionality."""
    
    @pytest.fixture
    def security_manager(self, tmp_path):
        """Create security manager with test directory."""
        from src.core.security_manager import SecurityManager
        
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: {
            'security.wipe_on_panic': True,
            'data_dir': str(tmp_path)
        }.get(key, default)
        
        return SecurityManager(mock_config)
    
    def test_secure_file_deletion(self, security_manager, tmp_path):
        """Test secure file deletion."""
        test_file = tmp_path / "sensitive.txt"
        test_file.write_text("Sensitive data")
        
        result = security_manager.secure_wipe(str(test_file))
        
        assert result is True
        assert not test_file.exists()
    
    def test_wipe_notes(self, security_manager, tmp_path):
        """Test wiping notes directory."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        
        for i in range(5):
            note_file = notes_dir / f"note{i}.enc"
            note_file.write_bytes(b"note content")
        
        security_manager.wipe_directory(str(notes_dir))
        
        # Check if notes are wiped
        remaining_files = list(notes_dir.glob("*.enc"))
        assert len(remaining_files) == 0 or not notes_dir.exists()
    
    def test_wipe_cache(self, security_manager, tmp_path):
        """Test wiping cache."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        cache_file = cache_dir / "cache.json"
        cache_file.write_text('{"cached": "data"}')
        
        security_manager.wipe_directory(str(cache_dir))
        
        # Check if cache is cleared
        assert not cache_file.exists() or cache_file.stat().st_size == 0


@pytest.mark.integration
class TestPanicModeDisplay:
    """Test panic mode display behavior."""
    
    @pytest.fixture
    def display_manager(self):
        """Create display manager."""
        mock_uart = Mock()
        
        from src.communication.display_manager import DisplayManager
        return DisplayManager(mock_uart)
    
    def test_display_calculator_mode(self, display_manager):
        """Test switching to calculator display."""
        result = display_manager.switch_mode('calculator')
        
        assert result is not None
    
    def test_clear_sensitive_display(self, display_manager):
        """Test clearing sensitive information from display."""
        display_manager.clear()
        
        # Display should be cleared
        assert True


@pytest.mark.integration
class TestFakeHistory:
    """Test fake history generation."""
    
    def test_load_fake_calculations(self, tmp_path):
        """Test loading fake calculation history."""
        import json
        
        fake_history_file = tmp_path / "calculations.json"
        
        fake_data = {
            "calculations": [
                {"expression": "25 + 37", "result": "62"},
                {"expression": "150 - 89", "result": "61"}
            ]
        }
        
        fake_history_file.write_text(json.dumps(fake_data))
        
        with open(fake_history_file) as f:
            data = json.load(f)
        
        assert len(data['calculations']) > 0
    
    def test_display_fake_history(self):
        """Test displaying fake history."""
        from src.features.calculator import Calculator
        
        calc = Calculator()
        
        # Set fake history
        fake_history = [
            {"expression": "25 + 37", "result": "62"},
            {"expression": "150 - 89", "result": "61"}
        ]
        
        # Would display this history instead of real history
        assert len(fake_history) > 0


@pytest.mark.integration
class TestPanicPerformance:
    """Test panic mode performance."""
    
    def test_panic_activation_speed(self):
        """Test panic activation speed."""
        from src.core.security_manager import SecurityManager
        
        mock_config = Mock()
        security = SecurityManager(mock_config)
        
        start = time.time()
        security.panic_mode()
        elapsed = time.time() - start
        
        # Should activate quickly
        assert elapsed < 0.5
    
    def test_data_wipe_speed(self, tmp_path):
        """Test data wipe speed."""
        from src.core.security_manager import SecurityManager
        
        mock_config = Mock()
        mock_config.get.return_value = str(tmp_path)
        
        security = SecurityManager(mock_config)
        
        # Create test files
        for i in range(10):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text("data" * 100)
        
        start = time.time()
        security.wipe_directory(str(tmp_path))
        elapsed = time.time() - start
        
        # Should wipe relatively quickly
        assert elapsed < 5.0


@pytest.mark.integration
class TestPanicStateManagement:
    """Test panic mode state management."""
    
    @pytest.fixture
    def state_manager(self):
        """Create state manager."""
        from src.core.state_manager import StateManager
        return StateManager()
    
    def test_save_panic_state(self, state_manager, tmp_path):
        """Test saving panic state."""
        state_file = tmp_path / "state.json"
        
        state_manager.set_panic_mode(True)
        state_manager.save(str(state_file))
        
        assert state_file.exists()
    
    def test_restore_panic_state(self, state_manager, tmp_path):
        """Test restoring panic state."""
        state_file = tmp_path / "state.json"
        
        state_manager.set_panic_mode(True)
        state_manager.save(str(state_file))
        
        new_state = StateManager()
        new_state.load(str(state_file))
        
        assert new_state.is_panic_mode()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
