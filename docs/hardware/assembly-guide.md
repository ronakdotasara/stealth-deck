# File 71: docs/hardware/assembly-guide.md

```markdown
# Stealth Deck - Assembly Guide

Step-by-step instructions for building your Stealth Deck.

---

## Before You Begin

### Required Skills
- Basic soldering (through-hole components)
- Wire stripping and crimping
- Multimeter usage
- Following wiring diagrams

### Tools Needed
- Soldering iron (60W recommended)
- Solder (lead-free or 60/40)
- Wire strippers
- Small Phillips screwdriver
- Multimeter
- Helping hands or PCB holder
- Tweezers
- Flush cutters
- Heat shrink tubing
- Hot glue gun

### Estimated Time
- **Beginner**: 4-6 hours
- **Intermediate**: 2-3 hours
- **Advanced**: 1-2 hours

---

## Safety First

⚠️ **Important Safety Notes:**
- Always wear safety glasses when soldering
- Work in a well-ventilated area
- Keep soldering iron in stand when not in use
- Check all connections before applying power
- Use proper ESD precautions
- Never exceed voltage ratings

---

## Step 1: Inventory Check

### Verify All Components

Use the [Bill of Materials](bom.csv) to check you have:

- [ ] ESP32 DevKit
- [ ] Raspberry Pi Zero 2W
- [ ] OLED Display (240×536px)
- [ ] 5×4 Matrix Keypad
- [ ] Pi Camera Module v2
- [ ] 18650 Battery + Holder
- [ ] Buck Converter (5V)
- [ ] LDO Regulator (3.3V)
- [ ] TP4056 Charger Module
- [ ] All resistors and capacitors
- [ ] Wires and connectors
- [ ] MicroSD card (32GB+)

---

## Step 2: Prepare the Perfboard

### Layout Planning

```
┌─────────────────────────────────────┐
│  [Display]                          │
│                                     │
│  [ESP32]        [Buck]    [LDO]    │
│                                     │
│  [Pi Zero]      [Battery Holder]   │
│                                     │
│  [Camera Cable]                     │
└─────────────────────────────────────┘
```

### Steps:

1. **Place Components**
   - Position components on perfboard
   - Leave 5mm spacing between components
   - Mark mounting holes with marker

2. **Cut Perfboard** (if needed)
   - Use a scoring tool or hacksaw
   - Smooth edges with sandpaper

---

## Step 3: Power Supply Assembly

### 3.1 - Battery Holder

1. Solder red wire to battery holder positive (+)
2. Solder black wire to negative (-)
3. Add heat shrink to connections
4. Test continuity with multimeter

### 3.2 - TP4056 Charger Module

```
Battery Holder → TP4056 Input
TP4056 Output  → Buck Converter Input
```

**Connections:**
- Battery (+) → B+ (TP4056)
- Battery (-) → B- (TP4056)
- OUT+ → Buck VIN
- OUT- → Common GND

### 3.3 - Buck Converter (5V for Pi)

1. **Adjust Output Voltage:**
   ```
   - Connect multimeter to OUT+ and OUT-
   - Apply power
   - Turn potentiometer until voltage = 5.0V
   - Disconnect power
   ```

2. **Wire Connections:**
   - VIN+ → TP4056 OUT+
   - VIN- → Common GND
   - VOUT+ → Pi 5V (Pin 2)
   - VOUT- → Pi GND (Pin 6)

### 3.4 - LDO Regulator (3.3V for ESP32)

1. **Identify Pins:**
   ```
   AMS1117-3.3 (SOT-223)
   
   Pin 1: GND
   Pin 2: VOUT (3.3V)
   Pin 3: VIN (5V)
   Tab: GND
   ```

2. **Solder to Perfboard:**
   - Add 100µF capacitor on input (VIN to GND)
   - Add 100µF capacitor on output (VOUT to GND)
   - Connect VIN to buck converter output
   - Connect VOUT to ESP32 VIN
   - Connect all grounds together

3. **Test Output:**
   - Apply power
   - Measure VOUT: Should be 3.25-3.35V
   - If incorrect, check connections

---

## Step 4: ESP32 Connections

### 4.1 - Solder Headers

1. Insert 2×19 pin headers into ESP32
2. Place ESP32 on perfboard (solder side up)
3. Solder all pins
4. Test continuity on a few pins

### 4.2 - OLED Display (I2C)

**Wiring:**
```
Display    ESP32      Wire Color
SDA    →   GPIO21     Blue
SCL    →   GPIO22     Yellow
VCC    →   3.3V       Red
GND    →   GND        Black
```

**Steps:**
1. Cut wires to length (10-15cm)
2. Strip 3mm from each end
3. Tin wire ends
4. Solder to display
5. Add heat shrink
6. Solder to ESP32 pins

### 4.3 - Matrix Keypad

**Row Connections:**
```
Keypad Row   ESP32 Pin
Row 1    →   GPIO13
Row 2    →   GPIO12
Row 3    →   GPIO14
Row 4    →   GPIO27
Row 5    →   GPIO26
```

**Column Connections:**
```
Keypad Col   ESP32 Pin
Col 1    →   GPIO25
Col 2    →   GPIO33
Col 3    →   GPIO32
Col 4    →   GPIO35
```

**Steps:**
1. Use ribbon cable for neat wiring
2. Label each wire with tape
3. Solder carefully (keypad pins delicate)
4. Add hot glue for strain relief

### 4.4 - UART to Raspberry Pi

**Connections:**
```
ESP32        Raspberry Pi
GPIO17 (TX)  →  GPIO15 (RX) - Pin 10
GPIO16 (RX)  →  GPIO14 (TX) - Pin 8
GND          →  GND - Pin 6
```

⚠️ **Note:** TX → RX crossover is correct!

**Steps:**
1. Use 3 separate wires (TX, RX, GND)
2. Keep wires short (<20cm)
3. Twist TX and RX together
4. Solder to ESP32 pins
5. Connect to Pi after Pi is mounted

---

## Step 5: Raspberry Pi Setup

### 5.1 - Prepare MicroSD Card

1. Download Raspberry Pi OS Lite (64-bit)
2. Flash to SD card using Raspberry Pi Imager
3. Create `ssh` file on boot partition
4. Create `wpa_supplicant.conf` (optional, for WiFi setup)
5. Insert SD card into Pi

### 5.2 - Mount Raspberry Pi

1. Position Pi on perfboard
2. Use M2.5 standoffs to elevate Pi
3. Secure with screws
4. Ensure no shorts underneath

### 5.3 - Camera Connection

1. Lift black latch on CSI connector
2. Insert ribbon cable (blue side toward USB ports)
3. Push latch down to secure
4. Route cable neatly

### 5.4 - Power Connection

**Connect to Buck Converter:**
```
Buck 5V+ → Pi Pin 2 (5V)
Buck GND → Pi Pin 6 (GND)
```

Use solid core wire (22 AWG) for power connections.

### 5.5 - UART Connection

Connect the three wires from ESP32:
```
ESP32 TX (GPIO17) → Pi Pin 10 (GPIO15 RX)
ESP32 RX (GPIO16) → Pi Pin 8 (GPIO14 TX)
ESP32 GND → Pi Pin 6 (GND)
```

---

## Step 6: Final Assembly

### 6.1 - Component Placement

Position all components for best fit:
- Display at top (visible)
- Keypad accessible
- Battery at bottom (weight distribution)
- ESP32 and Pi in center
- Camera facing forward

### 6.2 - Secure Components

1. **Hot Glue:**
   - Display corners
   - ESP32 edges
   - Battery holder
   - Keypad perimeter

2. **Cable Management:**
   - Use zip ties or twist ties
   - Route cables along edges
   - Avoid crossing over components

### 6.3 - Strain Relief

Add hot glue to:
- Display wire connections
- Keypad ribbon cable
- UART wires
- Camera ribbon cable

---

## Step 7: Pre-Power Testing

### 7.1 - Visual Inspection

Check for:
- [ ] No loose wires
- [ ] No solder bridges
- [ ] All connections secure
- [ ] Components properly oriented
- [ ] No exposed conductors touching

### 7.2 - Continuity Testing

Use multimeter to verify:
- [ ] Power rails continuous
- [ ] No shorts between 5V and GND
- [ ] No shorts between 3.3V and GND
- [ ] UART TX/RX not shorted
- [ ] I2C SDA/SCL not shorted

### 7.3 - Voltage Testing (No Battery)

1. Connect USB to TP4056 charger input
2. Measure buck converter output: **4.9-5.1V**
3. Measure LDO output: **3.25-3.35V**
4. If incorrect, stop and troubleshoot
5. Disconnect USB

---

## Step 8: First Power-On

### 8.1 - Insert Battery

1. Insert 18650 battery into holder
2. Observe for:
   - Smoke (stop immediately)
   - Unusual smells (stop immediately)
   - LED indicators on modules

### 8.2 - ESP32 Boot

1. ESP32 LED should light up
2. Display should show something (backlight on)
3. If not, check power and display connections

### 8.3 - Raspberry Pi Boot

1. Pi takes ~30 seconds to boot
2. Green LED should flicker (SD card activity)
3. Wait for boot to complete

### 8.4 - First Tests

1. **Display Test:**
   - Upload test sketch to ESP32
   - Should show text on display

2. **Keypad Test:**
   - Press keys
   - Serial monitor should show key codes

3. **UART Test:**
   - Send data from Pi to ESP32
   - Should appear on display

---

## Step 9: Software Installation

Follow the [Installation Guide](../INSTALLATION.md):

1. Flash ESP32 firmware via PlatformIO
2. SSH into Raspberry Pi
3. Run installation script
4. Configure API keys
5. Test all features

---

## Step 10: Enclosure (Optional)

### 3D Printed Case

1. Print case files from `hardware/enclosure/`
2. Test fit before gluing
3. Mount display and keypad
4. Secure electronics inside
5. Close and secure case

### DIY Enclosure

Materials:
- Project box (appropriate size)
- Drill for mounting holes
- Acrylic for display window

Steps:
1. Cut holes for display and keypad
2. Mount components
3. Secure lid

---

## Troubleshooting Assembly

### Display Not Working

**Check:**
1. I2C address (0x3C or 0x3D)
2. SDA/SCL connections
3. 3.3V power present
4. Run I2C scanner sketch

### Keypad Not Responding

**Check:**
1. All 9 wires connected
2. No solder bridges
3. Correct row/column mapping
4. Test continuity when key pressed

### UART Not Working

**Check:**
1. TX/RX crossover correct
2. Baud rate 115200 on both sides
3. Common ground connected
4. UART enabled on Pi

### Pi Won't Boot

**Check:**
1. SD card properly flashed
2. 5V power present (4.9-5.1V)
3. Green LED activity
4. Try different SD card

---

## Final Checklist

- [ ] All components secured
- [ ] No loose wires
- [ ] No shorts verified
- [ ] Voltages correct (3.3V and 5V)
- [ ] ESP32 boots and shows display
- [ ] Raspberry Pi boots
- [ ] UART communication working
- [ ] Camera detected
- [ ] Software installed
- [ ] All features tested
- [ ] Enclosure complete (if applicable)

---

## Congratulations! 🎉

You've successfully assembled your Stealth Deck!

**Next Steps:**
1. Read the [User Guide](../user-guide.md)
2. Configure settings
3. Test all modes
4. Practice panic mode
5. Join the community

---

## Need Help?

- **Documentation**: Check docs folder
- **Discord**: Community support
- **GitHub Issues**: Report problems
- **Email**: support@stealthdeck.com

---

**Assembly Guide Version**: 1.0  
**Last Updated**: 2025-11-24  
**Difficulty**: Intermediate  
**Success Rate**: 95% (with careful following)
```

