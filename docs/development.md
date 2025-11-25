# File 113: docs/development.md

```markdown
# Stealth Deck - Developer Guide

Complete guide for developers contributing to Stealth Deck.

---

## Development Environment Setup

### Prerequisites

**Required:**
- Linux development machine (or WSL2)
- Python 3.9+
- PlatformIO Core
- Git
- SSH access to Raspberry Pi

**Optional:**
- VS Code with PlatformIO extension
- Docker (for testing)
- Hardware debugger (ESP-PROG)

### Initial Setup

```
# Clone repository
git clone https://github.com/yourusername/stealth-deck.git
cd stealth-deck

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r raspberry-pi/requirements.txt
pip install -r raspberry-pi/requirements-dev.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

---

## Project Structure

```
stealth-deck/
├── esp32/                  # ESP32 firmware
│   ├── src/               # Source code
│   │   ├── display/       # Display drivers
│   │   ├── input/         # Input handling
│   │   ├── modes/         # Operating modes
│   │   ├── communication/ # UART/Bluetooth
│   │   └── utils/         # Utilities
│   ├── test/              # Unit tests
│   └── platformio.ini     # Build configuration
│
├── raspberry-pi/          # Raspberry Pi application
│   ├── src/               # Python source
│   │   ├── core/          # Core systems
│   │   ├── ai/            # AI integration
│   │   ├── features/      # Feature modules
│   │   ├── hardware/      # Hardware control
│   │   └── rendering/     # Text rendering
│   ├── tests/             # Unit tests
│   ├── scripts/           # Utility scripts
│   └── requirements.txt   # Dependencies
│
├── hardware/              # Hardware design
│   ├── schematics/        # KiCad schematics
│   ├── pcb/               # PCB layouts
│   └── enclosure/         # 3D models
│
├── docs/                  # Documentation
│   ├── software/          # Software docs
│   ├── hardware/          # Hardware docs
│   └── guides/            # User guides
│
└── tools/                 # Development tools
    ├── uart_monitor/      # UART debugging
    └── simulator/         # Hardware simulator
```

---

## Development Workflow

### 1. Creating a Feature Branch

```
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ...

# Commit with conventional commits
git commit -m "feat(module): add new feature"

# Push to remote
git push origin feature/your-feature-name
```

### 2. Running Tests

**ESP32 Tests:**
```
cd esp32
pio test
```

**Raspberry Pi Tests:**
```
cd raspberry-pi
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

**Integration Tests:**
```
cd raspberry-pi
pytest tests/integration/ -v
```

### 3. Code Quality Checks

**Linting:**
```
# Python
cd raspberry-pi
flake8 src/
pylint src/
black src/ --check

# Auto-format
black src/

# C++
cd esp32
pio check
```

**Type Checking:**
```
cd raspberry-pi
mypy src/
```

---

## ESP32 Development

### Building Firmware

```
cd esp32

# Build
pio run

# Build and upload
pio run -t upload

# Upload via OTA
pio run -t upload -e esp32_ota

# Clean build
pio run -t clean
```

### Serial Monitor

```
# Open serial monitor
pio device monitor

# With filters
pio device monitor --filter esp32_exception_decoder
```

### Debugging

```
# Debug with ESP-PROG
pio debug

# Debug with GDB
pio debug --interface=gdb
```

### Adding New Mode

1. Create mode header in `src/modes/`
2. Inherit from base mode class
3. Implement required methods:
   - `begin()`
   - `update()`
   - `handleKey()`
   - `render()`
4. Register in mode manager
5. Add tests

**Example:**
```
// src/modes/custom_mode.h
class CustomMode : public BaseMode {
public:
    CustomMode(DisplayDriver* d, KeypadDriver* k, UARTProtocol* u);
    
    void begin() override;
    void update() override;
    void handleKey(char key) override;
    void render() override;
};
```

---

## Raspberry Pi Development

### Running Development Server

```
cd raspberry-pi

# Run main application
python -m src.main

# Run with debug logging
LOGLEVEL=DEBUG python -m src.main

# Run specific module
python -m src.ai.gemini_client
```

### Adding New Feature

1. Create feature module in `src/features/`
2. Implement feature class
3. Register in feature manager
4. Add configuration options
5. Write tests
6. Update documentation

**Example:**
```
# src/features/custom_feature.py
class CustomFeature:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('custom_feature')
    
    def process(self, input_data):
        # Feature logic
        pass
```

### Database Migrations

```
# Create migration
alembic revision -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## UART Protocol

### Message Format

```
[START][TYPE][LEN_H][LEN_L][PAYLOAD...][CRC_H][CRC_L]
```

### Adding New Message Type

1. Define message type in both ESP32 and Pi
2. Implement encoder/decoder
3. Add handler function
4. Update protocol documentation
5. Add tests

**ESP32:**
```
// src/communication/uart_protocol.h
#define MSG_CUSTOM 0x20

bool sendCustomMessage(uint8_t* data, size_t len);
```

**Python:**
```
# src/communication/uart_handler.py
MSG_CUSTOM = 0x20

def send_custom_message(self, data: bytes):
    return self.send_message(MSG_CUSTOM, data)
```

---

## Testing Guidelines

### Unit Tests

**Test Structure:**
```
def test_feature():
    # Arrange
    feature = CustomFeature(config)
    
    # Act
    result = feature.process(input_data)
    
    # Assert
    assert result == expected
```

**Mocking:**
```
from unittest.mock import Mock, patch

@patch('module.external_dependency')
def test_with_mock(mock_dep):
    mock_dep.return_value = expected_value
    # Test code
```

### Integration Tests

```
@pytest.mark.integration
def test_end_to_end():
    # Test complete workflow
    pass
```

### Coverage Requirements

- Minimum 80% code coverage
- Critical paths must have 100% coverage
- All public APIs must be tested

---

## Performance Guidelines

### ESP32 Performance

**Memory:**
- Monitor heap usage: `ESP.getFreeHeap()`
- Avoid dynamic allocation in loops
- Use static buffers where possible

**CPU:**
- Keep loop() fast (<10ms per iteration)
- Use RTOS tasks for background work
- Optimize display updates

**Example:**
```
void loop() {
    unsigned long start = millis();
    
    // Loop code
    
    unsigned long elapsed = millis() - start;
    if (elapsed > 10) {
        Serial.printf("Loop slow: %lu ms\n", elapsed);
    }
}
```

### Python Performance

**Profiling:**
```
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

**Optimization:**
- Use generators for large datasets
- Cache expensive computations
- Async for I/O operations

---

## Documentation

### Code Documentation

**Python Docstrings:**
```
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description.
    
    Detailed description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input
    """
    pass
```

**C++ Comments:**
```
/**
 * Brief description.
 * 
 * Detailed description.
 * 
 * @param param1 Description
 * @param param2 Description
 * @return Description
 */
bool functionName(int param1, int param2);
```

### Documentation Updates

When adding features:
1. Update relevant .md files
2. Add code examples
3. Update API reference
4. Update changelog

---

## Debugging Tips

### Common Issues

**ESP32 Watchdog Reset:**
```
// Add in long-running loops
yield();  // or delay(1);
```

**UART Communication Errors:**
- Check baud rate matches
- Verify CRC calculation
- Add debug prints
- Use UART monitor tool

**Memory Leaks:**
```
# Use memory profiler
from memory_profiler import profile

@profile
def function_to_profile():
    pass
```

### Debug Logging

**ESP32:**
```
#ifdef DEBUG
  Serial.printf("Debug: %s\n", message);
#endif
```

**Python:**
```
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

---

## Release Process

### Version Numbering

Follow Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes

### Creating a Release

```
# Update version in files
# - esp32/platformio.ini
# - raspberry-pi/setup.py
# - VERSION file

# Update CHANGELOG.md

# Commit version bump
git commit -m "chore: bump version to x.y.z"

# Create tag
git tag -a vx.y.z -m "Release vx.y.z"

# Push
git push origin main --tags
```

---

## Contributing Guidelines

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guide
- Pull request process
- Issue reporting
- Community guidelines

---

## Resources

### Documentation
- [UART Protocol](software/uart-protocol.md)
- [P2P Protocol](software/p2p-protocol.md)
- [Hardware Guide](hardware/assembly-guide.md)

### External Resources
- [ESP32 Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [Gemini API Reference](https://ai.google.dev/docs)

---

**Version**: 1.0  
**Last Updated**: 2025-11-25  
**Maintainers**: Stealth Deck Development Team
```

