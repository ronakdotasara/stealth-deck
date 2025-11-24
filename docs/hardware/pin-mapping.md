# File 53: docs/hardware/pin-mapping.md

```markdown
# Stealth Deck - Pin Mapping & Connections

Complete pin assignment reference for ESP32 and Raspberry Pi Zero 2W.

---

## ESP32 DevKit Pin Mapping

### I2C - OLED Display

| ESP32 Pin | Function | Connection |
|-----------|----------|------------|
| GPIO21 | SDA | Display SDA |
| GPIO22 | SCL | Display SCL |
| 3.3V | Power | Display VCC |
| GND | Ground | Display GND |

**Notes:**
- Pull-up resistors (4.7kΩ) recommended for SDA/SCL
- Maximum I2C speed: 400kHz
- Display address: 0x3C or 0x3D

---

### Matrix Keypad (5×4)

#### Row Pins (Output)
| ESP32 Pin | Keypad Row | Keys |
|-----------|------------|------|
| GPIO13 | Row 1 | 1, 2, 3, + |
| GPIO12 | Row 2 | 4, 5, 6, - |
| GPIO14 | Row 3 | 7, 8, 9, × |
| GPIO27 | Row 4 | ., 0, =, ÷ |
| GPIO26 | Row 5 | FN, MODE, OK, FIX |

#### Column Pins (Input with Pull-up)
| ESP32 Pin | Keypad Column | Position |
|-----------|---------------|----------|
| GPIO25 | Column 1 | Left |
| GPIO33 | Column 2 | Mid-Left |
| GPIO32 | Column 3 | Mid-Right |
| GPIO35 | Column 4 | Right |

**Keypad Layout:**
```
   [+]
   [-]
   [×]
[.]  [=] [÷]
[FN][MD][OK][FX]
```

**Notes:**
- Internal pull-ups enabled on column pins
- Scan rate: 100Hz (10ms per scan)
- Debounce: 50ms
- Key codes: '0'-'9', '+', '-', '*', '/', '.', '=', '#', '*'

---

### UART - Raspberry Pi Communication

| ESP32 Pin | Function | Pi Pin | Pi GPIO |
|-----------|----------|--------|---------|
| GPIO17 (TX2) | UART TX | Pin 10 | GPIO15 (RX) |
| GPIO16 (RX2) | UART RX | Pin 8 | GPIO14 (TX) |
| GND | Ground | Pin 6 | GND |

**Settings:**
- Baud rate: 115200
- Data bits: 8
- Parity: None
- Stop bits: 1
- Flow control: None

**Notes:**
- TX/RX are crossed: ESP32 TX → Pi RX, ESP32 RX → Pi TX
- 3.3V logic level (compatible with Pi)
- Max cable length: 1 meter recommended

---

### Power & Status

| ESP32 Pin | Function | Connection |
|-----------|----------|------------|
| VIN (5V) | Power Input | LDO 3.3V Output |
| 3.3V | Power Output | Peripherals (max 600mA) |
| GND | Ground | Common Ground |
| EN | Enable | 10kΩ pull-up to 3.3V |
| GPIO2 | Built-in LED | Status indicator |
| GPIO0 | Boot Mode | 10kΩ pull-up (auto-boot) |

---

### Reserved/Unused Pins

| ESP32 Pin | Status | Notes |
|-----------|--------|-------|
| GPIO34-39 | Input Only | No internal pull-ups |
| GPIO6-11 | Flash | Do not use (connected to flash) |
| GPIO1, GPIO3 | UART0 | Used for programming/debug |

---

## Raspberry Pi Zero 2W Pin Mapping

### UART - ESP32 Communication

| Pi Pin | GPIO | Function | ESP32 Pin |
|--------|------|----------|-----------|
| Pin 8 | GPIO14 | UART TX | GPIO16 (RX2) |
| Pin 10 | GPIO15 | UART RX | GPIO17 (TX2) |
| Pin 6 | - | GND | GND |

**Configuration:**
```
# /boot/config.txt
enable_uart=1
dtoverlay=disable-bt
```

---

### Camera Interface (CSI)

| Connection | Pin/Cable | Notes |
|------------|-----------|-------|
| CSI Port | 15-pin ribbon | Camera Module v2/v3 |
| Cable Length | 15-30cm | Shorter is better |
| Orientation | Blue side up | On camera module |

**Supported Cameras:**
- Raspberry Pi Camera Module v2 (8MP)
- Raspberry Pi Camera Module v3 (12MP)
- Compatible IMX219/IMX477 modules

---

### I2C (Optional - Future Expansion)

| Pi Pin | GPIO | Function | Available For |
|--------|------|----------|---------------|
| Pin 3 | GPIO2 | I2C SDA | Sensors |
| Pin 5 | GPIO3 | I2C SCL | Sensors |

---

### Power

| Pi Pin | Function | Source | Voltage |
|--------|----------|--------|---------|
| Pin 2 | 5V Power | Buck Converter | 5.0V ±5% |
| Pin 4 | 5V Power | Buck Converter | 5.0V ±5% |
| Pin 6 | Ground | Common GND | 0V |

**Current Requirements:**
- Idle: 150-200mA @ 5V
- Active: 300-400mA @ 5V
- Peak: 500-600mA @ 5V (camera on)

---

## Power Distribution

### Battery to Buck Converter

| Connection | Voltage | Current |
|------------|---------|---------|
| Battery + | 3.7-4.2V | N/A |
| Battery - | GND | N/A |
| Buck Input | 3.7-4.2V | Up to 2A |

### Buck Converter (5V for Pi)

| Output | Voltage | Max Current | Load |
|--------|---------|-------------|------|
| 5V | 5.0V ±2% | 3A | Raspberry Pi |
| GND | 0V | - | Common Ground |

### LDO Regulator (3.3V for ESP32)

| Output | Voltage | Max Current | Load |
|--------|---------|-------------|------|
| 3.3V | 3.3V ±2% | 1A | ESP32 + Display |
| GND | 0V | - | Common Ground |

---

## Complete Wiring Diagram

```
18650 Li-ion Battery (3.7-4.2V)
        │
        ├──────► Buck Converter (5V, 3A)
        │            │
        │            └──────► Raspberry Pi Zero 2W
        │                         │
        │                         ├─ GPIO14/15 (UART) ◄─► ESP32 GPIO16/17
        │                         └─ CSI Port ◄─────────► Camera Module
        │
        └──────► LDO Regulator (3.3V, 1A)
                     │
                     └──────► ESP32 DevKit
                                  │
                                  ├─ GPIO21/22 (I2C) ◄─► OLED Display
                                  └─ GPIO13/12/14/27/26 ◄─► Keypad (Rows)
                                  └─ GPIO25/33/32/35 ◄─► Keypad (Cols)

All GND pins connected to common ground
```

---

## GPIO Summary Tables

### ESP32 GPIO Usage

| GPIO | Function | Direction | Mode |
|------|----------|-----------|------|
| 2 | Status LED | Output | Push-Pull |
| 12-14 | Keypad Rows | Output | Push-Pull |
| 16 | UART RX | Input | UART |
| 17 | UART TX | Output | UART |
| 21 | I2C SDA | I/O | Open-Drain |
| 22 | I2C SCL | Output | Open-Drain |
| 25 | Keypad Col | Input | Pull-Up |
| 26-27 | Keypad Rows | Output | Push-Pull |
| 32-33 | Keypad Cols | Input | Pull-Up |
| 35 | Keypad Col | Input | Pull-Up |

### Raspberry Pi GPIO Usage

| GPIO | Function | Alt Function | Used |
|------|----------|--------------|------|
| GPIO2 | I2C SDA | I2C1_SDA | ❌ Available |
| GPIO3 | I2C SCL | I2C1_SCL | ❌ Available |
| GPIO14 | UART TX | TXD0 | ✅ ESP32 |
| GPIO15 | UART RX | RXD0 | ✅ ESP32 |

---

## Connection Checklist

### Before Powering On

- [ ] All GND pins connected together
- [ ] Buck converter output = 5.0V (measure with multimeter)
- [ ] LDO output = 3.3V (measure with multimeter)
- [ ] UART TX/RX crossover correct (ESP TX → Pi RX, Pi TX → ESP RX)
- [ ] No short circuits between power and ground
- [ ] Display connected to correct I2C pins
- [ ] Keypad matrix wired correctly
- [ ] Camera ribbon cable properly seated
- [ ] Battery polarity correct
- [ ] All solder joints clean and secure

### After Power On

- [ ] ESP32 boots (LED blinks)
- [ ] Display shows boot screen
- [ ] Pi boots (takes ~30 seconds)
- [ ] UART communication works
- [ ] Keypad responds to presses
- [ ] Camera detected by Pi

---

## Voltage Levels Reference

| Component | Operating Voltage | Logic Level | Compatible |
|-----------|------------------|-------------|------------|
| ESP32 | 3.3V | 3.3V | ✅ |
| Raspberry Pi | 5V | 3.3V | ✅ |
| OLED Display | 3.3V | 3.3V | ✅ |
| Camera Module | 3.3V | 3.3V | ✅ |
| Keypad | 3.3V | 3.3V | ✅ |

**All components use 3.3V logic levels - direct connection safe!**

---

## Cable Lengths

| Connection | Recommended | Maximum | Notes |
|------------|-------------|---------|-------|
| UART (ESP-Pi) | 10-20cm | 100cm | Keep short for reliability |
| I2C (ESP-Display) | 5-15cm | 30cm | Use quality wires |
| Keypad Matrix | 5-10cm | 20cm | Ribbon cable preferred |
| Camera CSI | 15cm | 30cm | Official cables only |
| Power Wires | As needed | N/A | 22-24 AWG recommended |

---

## Testing Procedure

### Step 1: Power Test
```
# Measure voltages with multimeter
# Battery: 3.7-4.2V
# Buck output: 4.9-5.1V
# LDO output: 3.25-3.35V
```

### Step 2: ESP32 Test
```
# Upload test sketch
# Check serial monitor
# Verify display works
# Test keypad scanning
```

### Step 3: Raspberry Pi Test
```
# Boot Pi
# Check UART: ls /dev/serial0
# Test camera: libcamera-still -o test.jpg
# Verify I2C: i2cdetect -y 1
```

### Step 4: Communication Test
```
# Send data from Pi to ESP32
# Verify display updates
# Send keypress from ESP32 to Pi
# Check Pi receives data
```

---

## Common Issues

### Display Not Working
- Check I2C address (0x3C or 0x3D)
- Verify pull-up resistors
- Test with i2cdetect on Pi

### Keypad Not Responding
- Check row/column pin assignments
- Verify internal pull-ups enabled
- Test individual keys with multimeter

### UART Not Working
- Verify TX/RX crossover
- Check baud rate matches (115200)
- Ensure UART enabled on Pi

### Camera Not Detected
- Check ribbon cable orientation
- Verify CSI interface enabled
- Test with `vcgencmd get_camera`

---

**Last Updated**: 2025-11-24  
**Revision**: 1.0
`