"""
================================================================================
conftest.py - Pytest Configuration and Shared Fixtures
================================================================================
Version: 1.0.0
Date: 2025-11-24

Shared test fixtures and configuration for all tests.
================================================================================
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """Mock configuration manager."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        'api_keys.gemini_api_key': 'test_api_key',
        'hardware.uart_port': '/dev/ttyAMA0',
        'hardware.uart_baud': 115200,
        'hardware.camera_resolution': [1640, 1232],
        'ai.model': 'gemini-pro',
        'ai.vision_model': 'gemini-pro-vision',
        'ai.temperature': 0.7,
        'ai.max_tokens': 1024,
        'security.encryption_enabled': True,
        'security.wipe_on_panic': False,
        'storage.max_cache_size_mb': 100,
        'power.cpu_mode': 'balanced',
    }.get(key, default)
    return config


# ============================================================================
# Hardware Fixtures
# ============================================================================

@pytest.fixture
def mock_serial():
    """Mock serial port."""
    serial = Mock()
    serial.is_open = True
    serial.in_waiting = 0
    serial.read.return_value = b''
    serial.write.return_value = 0
    return serial


@pytest.fixture
def mock_camera():
    """Mock camera controller."""
    camera = Mock()
    camera.capture.return_value = '/tmp/test_image.jpg'
    camera.is_available.return_value = True
    return camera


@pytest.fixture
def mock_gpio():
    """Mock GPIO handler."""
    gpio = Mock()
    gpio.setup.return_value = None
    gpio.output.return_value = None
    gpio.input.return_value = 0
    return gpio


# ============================================================================
# Communication Fixtures
# ============================================================================

@pytest.fixture
def mock_uart_handler(mock_serial):
    """Mock UART handler."""
    from src.communication.uart_handler import UARTHandler
    
    with pytest.mock.patch('serial.Serial', return_value=mock_serial):
        handler = UARTHandler('/dev/ttyAMA0', 115200)
        handler.serial = mock_serial
        handler.connected = True
        return handler


@pytest.fixture
def mock_bluetooth():
    """Mock Bluetooth manager."""
    bt = Mock()
    bt.initialize.return_value = True
    bt.is_connected.return_value = False
    bt.send_data.return_value = True
    bt.receive_data.return_value = None
    return bt


# ============================================================================
# AI Fixtures
# ============================================================================

@pytest.fixture
def mock_gemini_client(mock_config):
    """Mock Gemini API client."""
    from src.ai.gemini_client import GeminiClient
    
    client = Mock(spec=GeminiClient)
    client.generate_text.return_value = "Mock AI response"
    client.analyze_image.return_value = "Mock image analysis"
    client.get_statistics.return_value = {
        'total_requests': 0,
        'cache_hits': 0,
        'errors': 0
    }
    return client


@pytest.fixture
def mock_gemini_renderer():
    """Mock Gemini renderer."""
    renderer = Mock()
    renderer.render.return_value = b'\x00' * 100
    renderer.render_text_simple.return_value = "Formatted text"
    return renderer


# ============================================================================
# Feature Fixtures
# ============================================================================

@pytest.fixture
def mock_notes_manager():
    """Mock notes manager."""
    notes = Mock()
    notes.create_note.return_value = Mock(id='test_note_id')
    notes.get_note.return_value = None
    notes.list_notes.return_value = []
    notes.delete_note.return_value = True
    return notes


@pytest.fixture
def mock_clipboard_manager():
    """Mock clipboard manager."""
    clipboard = Mock()
    clipboard.add.return_value = Mock(id='test_clip_id')
    clipboard.get_current.return_value = None
    clipboard.get_all.return_value = []
    clipboard.clear.return_value = None
    return clipboard


@pytest.fixture
def mock_search_engine():
    """Mock search engine."""
    search = Mock()
    search.search.return_value = [
        Mock(title='Result 1', url='http://example.com', snippet='Test')
    ]
    return search


@pytest.fixture
def mock_qr_generator():
    """Mock QR generator."""
    qr = Mock()
    qr.generate.return_value = '/tmp/qr_code.png'
    return qr


# ============================================================================
# Security Fixtures
# ============================================================================

@pytest.fixture
def mock_security_manager(mock_config):
    """Mock security manager."""
    security = Mock()
    security.panic_mode.return_value = None
    security.get_encryption_key.return_value = b'\x00' * 32
    security.hash_password.return_value = 'hashed_password'
    security.verify_password.return_value = True
    return security


@pytest.fixture
def encryption_key():
    """Test encryption key."""
    return b'\x00\x01\x02\x03' * 8  # 32 bytes


# ============================================================================
# State Fixtures
# ============================================================================

@pytest.fixture
def mock_state_manager():
    """Mock state manager."""
    state = Mock()
    state.get_state.return_value = 'idle'
    state.set_state.return_value = None
    state.get_mode.return_value = 'calculator'
    return state


@pytest.fixture
def mock_power_manager():
    """Mock power manager."""
    power = Mock()
    power.set_mode.return_value = True
    power.get_voltage.return_value = 3.7
    power.get_percentage.return_value = 75
    return power


# ============================================================================
# P2P Fixtures
# ============================================================================

@pytest.fixture
def mock_p2p_manager(mock_bluetooth, mock_gemini_client, mock_camera):
    """Mock P2P manager."""
    p2p = Mock()
    p2p.send_file.return_value = True
    p2p.receive_file.return_value = '/tmp/received_file.txt'
    p2p.send_text.return_value = True
    p2p.receive_text.return_value = "Received text"
    p2p.get_progress.return_value = {'progress': 50}
    return p2p


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_directory(tmp_path):
    """Create temporary directory for tests."""
    test_dir = tmp_path / "stealth_deck_test"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def temp_file(temp_directory):
    """Create temporary file for tests."""
    file_path = temp_directory / "test_file.txt"
    file_path.write_text("Test content")
    return file_path


@pytest.fixture
def test_image(temp_directory):
    """Create test image file."""
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='red')
    img_path = temp_directory / "test_image.jpg"
    img.save(img_path)
    return img_path


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_logger():
    """Mock logger."""
    logger = Mock()
    logger.debug.return_value = None
    logger.info.return_value = None
    logger.warning.return_value = None
    logger.error.return_value = None
    return logger


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return "This is a test message for the Stealth Deck system."


@pytest.fixture
def sample_markdown():
    """Sample markdown for testing."""
    return """
# Test Heading

This is **bold** and *italic* text.

- List item 1
- List item 2

def test():
pass

"""


# ============================================================================
# Test Data
# ============================================================================

@pytest.fixture
def sample_keypress_data():
    """Sample keypress data."""
    return {
        'key': '5',
        'state': True,
        'timestamp': 12345
    }


@pytest.fixture
def sample_battery_data():
    """Sample battery status data."""
    return {
        'voltage': 3.7,
        'percent': 75,
        'charging': False
    }


@pytest.fixture
def sample_search_results():
    """Sample search results."""
    return [
        {
            'title': 'Result 1',
            'url': 'https://example.com/1',
            'snippet': 'This is the first result'
        },
        {
            'title': 'Result 2',
            'url': 'https://example.com/2',
            'snippet': 'This is the second result'
        }
    ]


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "hardware: marks tests requiring hardware"
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    yield
    # Add singleton reset code here if needed


@pytest.fixture(autouse=True)
def cleanup_temp_files(temp_directory):
    """Cleanup temporary files after each test."""
    yield
    # Cleanup happens automatically with tmp_path


# ============================================================================
# Custom Assertions
# ============================================================================

class CustomAssertions:
    """Custom assertion helpers."""
    
    @staticmethod
    def assert_valid_crc(data, crc):
        """Assert CRC is valid."""
        from src.communication.uart_handler import UARTHandler
        handler = UARTHandler('/dev/null', 115200)
        calculated = handler._calculate_crc(data)
        assert calculated == crc, f"CRC mismatch: {calculated} != {crc}"
    
    @staticmethod
    def assert_valid_encryption(encrypted, original, key):
        """Assert encryption is valid."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        assert decrypted == original


@pytest.fixture
def assertions():
    """Provide custom assertions."""
    return CustomAssertions()
