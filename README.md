# File 25: raspberry-pi/README.md

```markdown
# Stealth Deck - Raspberry Pi Application

Complete Python application for the Raspberry Pi Zero 2W component of Stealth Deck.

## Overview

The Raspberry Pi handles all high-level AI processing, web scraping, image analysis, and data management for the Stealth Deck. It communicates with the ESP32 via UART for display/input operations.

## Features

- **AI Integration**: Google Gemini API for text generation and image analysis
- **Camera Control**: Pi Camera Module integration for image capture
- **UART Communication**: Binary protocol with ESP32 (115200 baud)
- **P2P Transfer**: Bluetooth file transfer between devices
- **Web Search**: Headless Google search scraping
- **Encrypted Storage**: AES-256-GCM encrypted notes and clipboard
- **Security**: Panic mode, secure wipe, encrypted communications
- **Power Management**: CPU frequency scaling, idle timeout

## Hardware Requirements

- Raspberry Pi Zero 2W (512MB RAM)
- Pi Camera Module (5MP or 8MP)
- MicroSD Card (32GB+ Class 10)
- UART connection to ESP32 (GPIO 14/15)

## Software Requirements

- Raspberry Pi OS (Bullseye or newer)
- Python 3.9+
- See `requirements.txt` for Python packages

## Installation

### Quick Install

```
cd raspberry-pi/scripts
sudo chmod +x install.sh
sudo ./install.sh
```

### Manual Install

```
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv \
    libcamera-dev python3-picamera2 bluez libbluetooth-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Copy configuration
sudo cp config/config.json.template /etc/stealth-deck/config.json

# Edit configuration
sudo nano /etc/stealth-deck/config.json
# Add your Gemini API key

# Install systemd service
sudo cp systemd/stealth-deck.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable stealth-deck
```

## Configuration

Edit `/etc/stealth-deck/config.json`:

```
{
  "api_keys": {
    "gemini_api_key": "YOUR_API_KEY_HERE"
  },
  "hardware": {
    "uart_port": "/dev/serial0",
    "uart_baud": 115200,
    "camera_resolution": 
  }
}
```

## Usage

### Start Service

```
sudo systemctl start stealth-deck
```

### Check Status

```
sudo systemctl status stealth-deck
```

### View Logs

```
sudo journalctl -u stealth-deck -f
```

### Stop Service

```
sudo systemctl stop stealth-deck
```

## Project Structure

```
raspberry-pi/
├── src/
│   ├── main.py                    # Main entry point
│   ├── core/                      # Core system modules
│   │   ├── config_manager.py      # Configuration management
│   │   ├── state_manager.py       # State management
│   │   ├── power_manager.py       # Power management
│   │   └── security_manager.py    # Security features
│   ├── communication/             # Communication modules
│   │   ├── uart_handler.py        # UART protocol
│   │   └── bluetooth_manager.py   # Bluetooth P2P
│   ├── hardware/                  # Hardware interfaces
│   │   ├── camera_controller.py   # Camera control
│   │   └── battery_monitor.py     # Battery monitoring
│   ├── ai/                        # AI modules
│   │   ├── gemini_client.py       # Gemini API client
│   │   └── gemini_renderer.py     # Text rendering
│   ├── features/                  # Feature modules
│   │   ├── search_engine.py       # Web search
│   │   ├── clipboard_manager.py   # Clipboard
│   │   ├── notes_manager.py       # Encrypted notes
│   │   └── qr_generator.py        # QR codes
│   ├── p2p/                       # P2P modules
│   │   └── p2p_manager.py         # P2P transfer
│   └── utils/                     # Utilities
│       ├── logger.py              # Logging
│       └── memory_monitor.py      # Memory management
├── config/
│   └── config.json.template       # Configuration template
├── systemd/
│   └── stealth-deck.service       # Systemd service
├── scripts/
│   └── install.sh                 # Installation script
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Development

### Running Locally

```
source venv/bin/activate
python src/main.py --debug
```

### Testing

```
pytest tests/
```

### Linting

```
flake8 src/
pylint src/
```

## API Keys

### Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to config: `api_keys.gemini_api_key`

## Troubleshooting

### UART Not Working

```
# Check UART is enabled
ls /dev/serial0

# Enable UART in config.txt
sudo nano /boot/config.txt
# Add: enable_uart=1

# Disable serial console
sudo raspi-config
# Interface Options -> Serial Port -> No (login shell)
# Yes (serial hardware)
```

### Camera Not Working

```
# Check camera is connected
vcgencmd get_camera

# Enable camera
sudo raspi-config
# Interface Options -> Camera -> Enable

# Install libcamera
sudo apt-get install -y libcamera-apps python3-picamera2
```

### Bluetooth Not Working

```
# Check Bluetooth status
sudo systemctl status bluetooth

# Restart Bluetooth
sudo systemctl restart bluetooth

# Make device discoverable
bluetoothctl
power on
discoverable on
```

### High Memory Usage

The Pi Zero 2W has limited RAM (512MB). If memory usage is high:

```
# Check memory
free -h

# Clear caches
sudo sync
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# Reduce cache size in config
# Set: storage.max_cache_size_mb to lower value
```

## Performance Optimization

### CPU Frequency

```
# Check current frequency
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq

# Set governor
sudo apt-get install -y cpufrequtils
sudo cpufreq-set -g performance
```

### Swap

```
# Increase swap size
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set: CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Security

### Encrypted Storage

All sensitive data is encrypted using AES-256-GCM:

- Notes: Encrypted at rest
- Clipboard: Encrypted at rest
- Config: Contains API keys (protect with file permissions)

### Panic Mode

Emergency data wipe on panic signal:

```
# Configure in config.json
"security": {
  "wipe_on_panic": true
}
```

### Secure Deletion

```
# Install secure-delete
sudo apt-get install -y secure-delete

# Securely delete file
srm -v file.txt
```

## Contributing

See main project CONTRIBUTING.md

## License

MIT License - See LICENSE file

## Support

- Issues: GitHub Issues
- Documentation: Project Wiki
- Discussions: GitHub Discussions

## Credits

- Google Gemini API
- picamera2 library
- PyBluez
- All contributors

---

**⚠️ Warning**: This device handles sensitive data. Always ensure proper security measures are in place.
```

***

# File 26: raspberry-pi/.gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
*.log
logs/
/var/log/stealth-deck/

# Configuration with secrets
config/config.json
/etc/stealth-deck/config.json

# Data directories
data/
/var/lib/stealth-deck/

# Temporary files
tmp/
temp/
*.tmp
/tmp/stealth-deck/

# Test coverage
.coverage
htmlcov/
.pytest_cache/
.tox/

# Distribution
*.tar.gz
*.zip

# Compiled files
*.pyc

# Jupyter Notebook
.ipynb_checkpoints

# Environment variables
.env
.env.local

# Database
*.db
*.sqlite

# OS
Thumbs.db

# Backup files
*.bak
*.backup

# Camera captures
captures/
*.jpg
*.jpeg
*.png

# Cache
cache/
*.cache

# Encrypted files
*.enc
*.aes

# API keys
*.key
*.pem
```