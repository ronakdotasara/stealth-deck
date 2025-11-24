text
# Stealth Deck - Troubleshooting Guide

Common issues and solutions for Stealth Deck.

---

## Quick Diagnostics

### Check System Status

Raspberry Pi
sudo systemctl status stealth-deck
journalctl -u stealth-deck -n 50

Check UART
ls /dev/serial0

Check camera
vcgencmd get_camera

text

### LED Indicators

| LED Pattern | Meaning | Action |
|-------------|---------|--------|
| Solid | Normal operation | None |
| Slow blink | Processing | Wait |
| Fast blink | Error | Check logs |
| Off | No power / Sleep | Check power |

---

## Hardware Issues

### Display Not Working

**Symptoms:** Blank screen, no output

**Solutions:**
1. Check I2C connection
i2cdetect -y 1

Should show 0x3C or 0x3D
text

2. Verify wiring:
   - SDA → GPIO21
   - SCL → GPIO22
   - VCC → 3.3V
   - GND → GND

3. Test display:
// In Arduino IDE
#include <Wire.h>
Wire.begin(21, 22);
Wire.beginTransmission(0x3C);
int error = Wire.endTransmission();
Serial.println(error == 0 ? "OK" : "FAIL");

text

### Keypad Not Responding

**Symptoms:** Keys don't register

**Solutions:**
1. Check pull-up resistors enabled
2. Verify pin connections
3. Test individual keys with multimeter
4. Adjust debounce delay in code

### UART Communication Failed

**Symptoms:** No data between ESP32 and Pi

**Solutions:**
1. **Verify crossover**: TX → RX, RX → TX
2. **Check baud rate**: Both 115200
3. **Common ground**: GND connected
4. **Enable UART on Pi**:
sudo raspi-config

Interface → Serial → No (console), Yes (hardware)
sudo reboot

text

5. **Test communication**:
On Pi
echo "test" > /dev/serial0

text

### Camera Not Detected

**Symptoms:** `vcgencmd get_camera` shows `supported=0`

**Solutions:**
1. Enable camera:
sudo raspi-config

Interface → Camera → Enable
sudo reboot

text

2. Check ribbon cable:
   - Proper orientation (blue side up)
   - Firmly seated in connector
   - No damage to cable

3. Test camera:
libcamera-still -o test.jpg

text

---

## Software Issues

### Service Won't Start

**Error:** `systemctl start stealth-deck` fails

**Solutions:**
1. Check logs:
journalctl -u stealth-deck -xe

text

2. Verify Python environment:
cd /opt/stealth-deck
source venv/bin/activate
python src/main.py --debug

text

3. Check permissions:
sudo chown -R stealth-deck:stealth-deck /opt/stealth-deck
sudo chmod +x /opt/stealth-deck/venv/bin/python

text

### Gemini API Errors

**Error:** `API key invalid` or `Rate limit exceeded`

**Solutions:**
1. Verify API key:
sudo nano /etc/stealth-deck/config.json

Check gemini_api_key is correct
text

2. Test API key:
curl -H "Content-Type: application/json"
-d '{"contents":[{"parts":[{"text":"test"}]}]}'
"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=YOUR_KEY"

text

3. Check quota: Visit Google AI Studio

### Memory Issues

**Symptoms:** System freezes, out of memory errors

**Solutions:**
1. Check memory usage:
free -h

text

2. Reduce cache size:
{
"storage": {
"max_cache_size_mb": 50
}
}

text

3. Enable swap:
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile

Set CONF_SWAPSIZE=512
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

text

---

## Performance Issues

### Slow AI Responses

**Symptoms:** Queries take >10 seconds

**Solutions:**
1. Check internet speed
2. Enable response caching
3. Use WiFi instead of mobile hotspot
4. Reduce image resolution for vision queries

### Display Lag

**Symptoms:** Slow screen refresh

**Solutions:**
1. Reduce I2C frequency
2. Optimize text rendering
3. Use display buffer efficiently
4. Lower display refresh rate

### Battery Draining Fast

**Solutions:**
1. Lower brightness
2. Enable auto-sleep
3. Disable Bluetooth when not in use
4. Use power save mode
5. Check for stuck processes

---

## Connection Issues

### Bluetooth Pairing Failed

**Solutions:**
1. Restart Bluetooth:
sudo systemctl restart bluetooth
sudo hciconfig hci0 down
sudo hciconfig hci0 up

text

2. Clear paired devices:
sudo bluetoothctl
remove <device_address>

text

3. Re-pair devices

### WiFi Not Connecting

**Solutions:**
1. Check credentials
2. Verify 2.4GHz network (Pi Zero doesn't support 5GHz)
3. Check signal strength
4. Restart WiFi:
sudo systemctl restart dhcpcd

text

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| E001 | UART timeout | Check connections |
| E002 | CRC error | Retry transmission |
| E003 | Invalid message | Check protocol |
| E004 | Camera error | Restart camera |
| E005 | API error | Check API key |
| E006 | Memory error | Free memory |
| E007 | Storage full | Clear cache |

---

## Recovery Procedures

### Soft Reset

sudo systemctl restart stealth-deck

text

### Hard Reset

1. Power off device
2. Wait 10 seconds
3. Power on

### Factory Reset

**WARNING: Erases all data!**

sudo /opt/stealth-deck/scripts/factory_reset.sh

text

---

## Getting Help

### Before Asking

1. Check this troubleshooting guide
2. Search existing issues on GitHub
3. Check documentation
4. Enable debug logging

### Where to Ask

- **GitHub Issues**: For bugs and features
- **Discord**: For quick questions
- **Email**: support@stealthdeck.com

### Information to Provide

1. Hardware version
2. Software version (`cat /opt/stealth-deck/VERSION`)
3. Error messages (copy from logs)
4. Steps to reproduce
5. Expected vs actual behavior

---

**Last Updated**: 2025-11-24