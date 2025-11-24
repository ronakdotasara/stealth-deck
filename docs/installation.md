# File 42: docs/INSTALLATION.md

```markdown
# Stealth Deck - Installation Guide

Complete installation guide for building and deploying Stealth Deck.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Hardware Assembly](#hardware-assembly)
3. [ESP32 Setup](#esp32-setup)
4. [Raspberry Pi Setup](#raspberry-pi-setup)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

- ESP32 DevKit (ESP32-WROOM-32)
- Raspberry Pi Zero 2W
- OLED Display (240×536, SSD1306)
- 5×4 Matrix Keypad
- Raspberry Pi Camera Module v2/v3
- 18650 Li-ion Battery (3000-5000mAh)
- Buck Converter (5V, 3A)
- LDO Regulator (3.3V, 1A)
- MicroSD Card (32GB+, Class 10)
- USB cables and wires

### Software Requirements

**Development Computer:**
- Python 3.9+
- PlatformIO CLI or VSCode with PlatformIO extension
- Git

**Raspberry Pi:**
- Raspberry Pi OS (Bullseye or newer)
- Internet connection for initial setup

---

## Hardware Assembly

### Step 1: Prepare Components

1. **Test each component individually** before assembly
2. **Label wires** to avoid confusion
3. **Use proper insulation** on all connections

### Step 2: Power Supply

```
18650 Battery (3.7-4.2V)
    │
    ├─── Buck Converter (5V) ──► Raspberry Pi Zero 2W
    │
    └─── LDO Regulator (3.3V) ──► ESP32 DevKit
```

**Wiring:**
- Battery (+) → Buck Converter VIN
- Battery (-) → Common Ground
- Buck Output (5V) → Pi 5V Pin
- LDO Output (3.3V) → ESP32 VIN
- All grounds connected together

### Step 3: ESP32 Connections

#### OLED Display (I2C)
```
ESP32          OLED Display
GPIO21 (SDA) → SDA
GPIO22 (SCL) → SCL
3.3V         → VCC
GND          → GND
```

#### Matrix Keypad
```
ESP32    Keypad
GPIO13 → Row 1
GPIO12 → Row 2
GPIO14 → Row 3
GPIO27 → Row 4
GPIO26 → Row 5

GPIO25 → Col 1
GPIO33 → Col 2
GPIO32 → Col 3
GPIO35 → Col 4
```

#### UART to Raspberry Pi
```
ESP32     Raspberry Pi
GPIO17 → GPIO14 (TX)
GPIO16 → GPIO15 (RX)
GND    → GND
```

### Step 4: Raspberry Pi Connections

#### Camera Module
- Connect via CSI ribbon cable
- Ensure cable is properly seated

#### UART to ESP32
- Already connected in Step 3

### Step 5: Final Assembly Checklist

- [ ] All power connections secure
- [ ] UART crossover correct (ESP32 TX → Pi RX, ESP32 RX → Pi TX)
- [ ] Common ground between all components
- [ ] Display properly connected
- [ ] Keypad matrix wired correctly
- [ ] Camera ribbon cable seated
- [ ] No short circuits (test with multimeter)

---

## ESP32 Setup

### Install PlatformIO

**Option 1: VSCode Extension**
1. Install VSCode
2. Install PlatformIO IDE extension
3. Restart VSCode

**Option 2: CLI**
```
pip install platformio
```

### Flash Firmware

```
# Clone repository
git clone https://github.com/yourusername/stealth-deck.git
cd stealth-deck/esp32

# Build firmware
pio run

# Upload to ESP32
pio run -t upload

# Monitor serial output (optional)
pio device monitor
```

### Verify Installation

1. Power on ESP32
2. Display should show "Stealth Deck" boot screen
3. Keypad should respond to button presses
4. Serial monitor should show initialization logs

---

## Raspberry Pi Setup

### Prepare SD Card

1. **Download Raspberry Pi OS Lite** (64-bit recommended)
2. **Flash to SD card** using Raspberry Pi Imager
3. **Enable SSH** (create empty `ssh` file on boot partition)
4. **Configure WiFi** (optional, create `wpa_supplicant.conf`)

```
# wpa_supplicant.conf
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourWiFiSSID"
    psk="YourPassword"
    key_mgmt=WPA-PSK
}
```

### Initial Boot

1. Insert SD card into Pi
2. Power on
3. Find Pi's IP address (check router or use `nmap`)
4. SSH into Pi: `ssh pi@<IP_ADDRESS>`
5. Default password: `raspberry`

### Change Default Password

```
passwd
```

### Run Installation Script

```
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Clone repository
git clone https://github.com/yourusername/stealth-deck.git
cd stealth-deck/raspberry-pi

# Run installation script
sudo chmod +x scripts/install.sh
sudo ./scripts/install.sh
```

The script will:
- ✅ Install system dependencies
- ✅ Create virtual environment
- ✅ Install Python packages
- ✅ Configure UART
- ✅ Enable camera
- ✅ Setup Bluetooth
- ✅ Install systemd service
- ✅ Create directories

**Reboot after installation:**
```
sudo reboot
```

---

## Configuration

### API Keys

1. **Get Gemini API Key:**
   - Visit https://makersuite.google.com/app/apikey
   - Create new API key
   - Copy key

2. **Edit configuration:**
```
sudo nano /etc/stealth-deck/config.json
```

3. **Add API key:**
```
{
  "api_keys": {
    "gemini_api_key": "YOUR_ACTUAL_API_KEY_HERE"
  }
}
```

### Hardware Configuration

Edit `/etc/stealth-deck/config.json`:

```
{
  "hardware": {
    "uart_port": "/dev/serial0",
    "uart_baud": 115200,
    "camera_resolution": 
  }
}
```

### Security Settings

```
{
  "security": {
    "panic_key_combo": "FN+FIX",
    "unlock_sequence": "FN+5+5+5",
    "wipe_on_panic": false,
    "encryption_enabled": true
  }
}
```

**⚠️ Warning:** Set `wipe_on_panic: true` only if you want data deleted on panic!

---

## Testing

### Test ESP32

```
# Connect to ESP32 serial
pio device monitor -b 115200
```

Expected output:
```
[INFO] Stealth Deck v1.0.0
[INFO] Display initialized
[INFO] Keypad initialized
[INFO] UART initialized
[INFO] System ready
```

### Test Raspberry Pi Service

```
# Check service status
sudo systemctl status stealth-deck

# View logs
sudo journalctl -u stealth-deck -f

# Test manually
cd /opt/stealth-deck
source venv/bin/activate
python src/main.py --debug
```

### Test Communication

1. Press keys on keypad
2. Check Pi logs for keypress events
3. Send test message from Pi to display

### Test Camera

```
# Capture test image
libcamera-still -o test.jpg

# Check image
ls -lh test.jpg
```

### Test AI

1. Unlock device (FN+5+5+5)
2. Enter text query
3. Press OK
4. Check for Gemini response

---

## Troubleshooting

### ESP32 Issues

**Display not working:**
```
# Check I2C connection
pio device monitor
# Look for "Display initialized" message
```

**Keypad not responding:**
- Check GPIO connections
- Verify pin mappings in `config.h`
- Test individual keys

**UART not working:**
- Verify TX/RX crossover
- Check baud rate (115200)
- Ensure common ground

### Raspberry Pi Issues

**Service won't start:**
```
# Check logs
sudo journalctl -u stealth-deck -n 50

# Test manually
cd /opt/stealth-deck
source venv/bin/activate
python src/main.py
```

**UART not available:**
```
# Check UART is enabled
ls /dev/serial0

# If missing, enable in config
sudo raspi-config
# Interface Options → Serial Port → No (login) → Yes (hardware)
```

**Camera not working:**
```
# Check camera
vcgencmd get_camera

# Should show: supported=1 detected=1

# Enable camera
sudo raspi-config
# Interface Options → Camera → Enable
```

**Gemini API errors:**
- Verify API key is correct
- Check internet connection
- Review API quota

**High memory usage:**
```
# Check memory
free -h

# Reduce cache size in config
sudo nano /etc/stealth-deck/config.json
# Set: storage.max_cache_size_mb to lower value
```

### Common Errors

**"Permission denied" on UART:**
```
sudo usermod -a -G dialout $USER
sudo reboot
```

**"Module not found" errors:**
```
source /opt/stealth-deck/venv/bin/activate
pip install -r requirements.txt
```

**Bluetooth not working:**
```
sudo systemctl restart bluetooth
sudo hciconfig hci0 up
```

---

## Post-Installation

### Enable Auto-Start

```
sudo systemctl enable stealth-deck
```

### Create Backup

```
# Backup configuration
sudo cp /etc/stealth-deck/config.json ~/config.json.backup

# Backup SD card (from computer)
sudo dd if=/dev/sdX of=stealth-deck-backup.img bs=4M status=progress
```

### Update System

```
cd /opt/stealth-deck
git pull
sudo systemctl restart stealth-deck
```

---

## Next Steps

- Read [User Guide](user-guide.md)
- Review [Security Features](software/security.md)
- Check [Troubleshooting Guide](troubleshooting.md)
- Join [Discord Community](https://discord.gg/stealthdeck)

---

**Installation Complete!** 🎉
