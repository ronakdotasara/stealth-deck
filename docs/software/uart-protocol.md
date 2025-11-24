# File 63: docs/software/uart-protocol.md

```markdown
# Stealth Deck - UART Protocol Specification

Complete specification for the UART communication protocol between ESP32 and Raspberry Pi.

---

## Protocol Overview

### Purpose

The UART protocol enables reliable binary communication between the ESP32 (UI controller) and Raspberry Pi (AI processor) for command exchange, data transfer, and status updates.

### Key Features

- Binary framing with start marker
- CRC16-CCITT error detection
- Variable-length messages (0-1024 bytes)
- 14 message types
- ACK/NACK acknowledgments
- Flow control via handshaking

### Physical Layer

| Parameter | Value |
|-----------|-------|
| Baud Rate | 115200 |
| Data Bits | 8 |
| Parity | None |
| Stop Bits | 1 |
| Flow Control | None (software) |
| TX Pin (ESP32) | GPIO17 |
| RX Pin (ESP32) | GPIO16 |
| TX Pin (Pi) | GPIO14 |
| RX Pin (Pi) | GPIO15 |

---

## Message Format

### Frame Structure

```
┌──────┬──────────┬──────────┬──────────┬─────────┬─────────┬─────────┐
│START │ MSG_TYPE │ LENGTH_H │ LENGTH_L │ PAYLOAD │ CRC16_H │ CRC16_L │
│ 0xAA │ 1 byte   │ 1 byte   │ 1 byte   │ 0-1024  │ 1 byte  │ 1 byte  │
└──────┴──────────┴──────────┴──────────┴─────────┴─────────┴─────────┘
  Byte:    0          1          2          3        4..N      N+1      N+2
```

### Field Descriptions

#### START (1 byte)
- **Value**: `0xAA` (170 decimal)
- **Purpose**: Frame synchronization marker
- **Note**: All messages must start with this byte

#### MSG_TYPE (1 byte)
- **Range**: 0x01 to 0xFF
- **Purpose**: Identifies message type
- **See**: Message Types section

#### LENGTH_H, LENGTH_L (2 bytes)
- **Encoding**: Big-endian (network byte order)
- **Range**: 0 to 1024
- **Purpose**: Payload length in bytes
- **Calculation**: `length = (LENGTH_H << 8) | LENGTH_L`

#### PAYLOAD (0-1024 bytes)
- **Content**: Message-specific data
- **Format**: Varies by message type
- **Maximum**: 1024 bytes per message

#### CRC16_H, CRC16_L (2 bytes)
- **Algorithm**: CRC16-CCITT (polynomial 0x1021)
- **Initial**: 0xFFFF
- **Encoding**: Big-endian
- **Calculated over**: MSG_TYPE + LENGTH + PAYLOAD
- **Purpose**: Error detection

---

## Message Types

### Control Messages

#### 0x01 - Display Text (Pi → ESP32)
Display text message on OLED screen.

**Payload Format:**
```
┌──────────────────┬──────────────────┐
│ TEXT_LENGTH (2)  │ TEXT_DATA (N)    │
└──────────────────┴──────────────────┘
```

**Example:**
```
// "Hello World"
0xAA 0x01 0x00 0x0D 0x00 0x0B 'H' 'e' 'l' 'l' 'o' ' ' 
'W' 'o' 'r' 'l' 'd' [CRC_H] [CRC_L]
```

#### 0x02 - Display Image (Pi → ESP32)
Display image data on OLED screen.

**Payload Format:**
```
┌──────────┬──────────┬──────────┬──────────────┐
│ WIDTH(2) │ HEIGHT(2)│FORMAT(1) │ IMAGE_DATA   │
└──────────┴──────────┴──────────┴──────────────┘

FORMAT:
  0x00 = Monochrome (1 bit per pixel)
  0x01 = Grayscale (8 bits per pixel)
```

#### 0x03 - Keypress Event (ESP32 → Pi)
Send keypress from ESP32 to Pi.

**Payload Format:**
```
┌──────────┬──────────┬──────────────┐
│ KEY(1)   │ STATE(1) │ TIMESTAMP(4) │
└──────────┴──────────┴──────────────┘

KEY: ASCII character ('0'-'9', '+', '-', etc.)
STATE: 0x00 = Released, 0x01 = Pressed
TIMESTAMP: Milliseconds since boot
```

#### 0x04 - Camera Capture Request (ESP32 → Pi)
Request camera to capture image.

**Payload Format:**
```
┌────────────┬────────────┬──────────┐
│ WIDTH (2)  │ HEIGHT (2) │ FLAGS(1) │
└────────────┴────────────┴──────────┘

FLAGS:
  Bit 0: Auto-analyze (1 = send to Gemini)
  Bit 1: Save to disk
  Bit 2-7: Reserved
```

#### 0x05 - Mode Change (Bidirectional)
Change operating mode.

**Payload Format:**
```
┌──────────┐
│ MODE (1) │
└──────────┘

MODE:
  0x00 = Calculator Mode
  0x01 = Smart Mode
  0x02 = P2P Mode
  0x03 = WiFi Sniffer Mode
  0x04 = Settings Mode
```

#### 0x06 - Panic Signal (ESP32 → Pi)
Emergency panic mode activation.

**Payload Format:**
```
┌───────────┐
│ REASON(1) │
└───────────┘

REASON:
  0x00 = Key combo (FN+FIX)
  0x01 = Timeout
  0x02 = External trigger
```

#### 0x07 - Heartbeat (Bidirectional)
Keep-alive message.

**Payload Format:**
```
┌──────────────┬──────────┐
│ TIMESTAMP(4) │ STATUS(1)│
└──────────────┴──────────┘

STATUS:
  0x00 = OK
  0x01 = Busy
  0x02 = Error
```

#### 0x08 - Battery Status (ESP32 → Pi)
Battery level and charging status.

**Payload Format:**
```
┌──────────┬──────────┬──────────┐
│VOLTAGE(2)│PERCENT(1)│ FLAGS(1) │
└──────────┴──────────┴──────────┘

VOLTAGE: Battery voltage in millivolts
PERCENT: Battery percentage (0-100)
FLAGS:
  Bit 0: Charging
  Bit 1: Low battery
  Bit 2: Critical battery
```

### Response Messages

#### 0x0A - ACK (Bidirectional)
Acknowledge successful message receipt.

**Payload Format:**
```
┌────────────┐
│ MSG_ID (1) │
└────────────┘

MSG_ID: Type of message being acknowledged
```

#### 0x0B - NACK (Bidirectional)
Negative acknowledgment (error).

**Payload Format:**
```
┌────────────┬────────────┐
│ MSG_ID (1) │ ERROR (1)  │
└────────────┴────────────┘

ERROR:
  0x01 = CRC Error
  0x02 = Invalid message type
  0x03 = Payload too large
  0x04 = Processing error
```

### Data Transfer Messages

#### 0x10 - File Transfer Start (Bidirectional)
Initiate file transfer.

**Payload Format:**
```
┌──────────────┬────────────┬──────────────┬──────────┐
│ FILE_SIZE(4) │ CHUNKS(2)  │ NAME_LEN(1)  │ FILENAME │
└──────────────┴────────────┴──────────────┴──────────┘
```

#### 0x11 - File Chunk (Bidirectional)
Send file data chunk.

**Payload Format:**
```
┌────────────┬────────────┬──────────────┐
│ CHUNK_ID(2)│ SIZE (2)   │ CHUNK_DATA   │
└────────────┴────────────┴──────────────┘

CHUNK_SIZE: Maximum 1024 bytes per chunk
```

#### 0x12 - File Transfer Complete (Bidirectional)
Signal file transfer completion.

**Payload Format:**
```
┌────────────┬──────────┐
│ CRC32 (4)  │STATUS(1) │
└────────────┴──────────┘

STATUS:
  0x00 = Success
  0x01 = Failed
```

---

## CRC16-CCITT Calculation

### Algorithm

```
Polynomial: 0x1021
Initial:    0xFFFF
XOR Out:    0x0000
Reflect In:  No
Reflect Out: No
```

### Pseudo-code

```
def crc16_ccitt(data):
    crc = 0xFFFF
    
    for byte in data:
        crc ^= (byte << 8)
        
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            
            crc &= 0xFFFF
    
    return crc
```

### C Implementation

```
uint16_t crc16_ccitt(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    
    for (size_t i = 0; i < length; i++) {
        uint8_t x = (crc >> 8) ^ data[i];
        x ^= x >> 4;
        crc = (crc << 8) ^ (x << 12) ^ (x << 5) ^ x;
    }
    
    return crc;
}
```

---

## Communication Flow

### Successful Message Exchange

```
ESP32                                   Raspberry Pi
  │                                           │
  ├─────── Display Text (0x01) ─────────────►│
  │                                           │
  │                                    [Process]
  │                                           │
  │◄──────────── ACK (0x0A) ──────────────────┤
  │                                           │
```

### Failed Message (CRC Error)

```
ESP32                                   Raspberry Pi
  │                                           │
  ├─────── Display Text (0x01) ─────────────►│
  │              [CRC ERROR]                  │
  │                                           │
  │◄──────────── NACK (0x0B) ─────────────────┤
  │           (ERROR = 0x01)                  │
  │                                           │
  ├─────── Display Text (0x01) ─────────────►│ [Retry]
  │                                           │
  │◄──────────── ACK (0x0A) ──────────────────┤
  │                                           │
```

### File Transfer Flow

```
Sender                                    Receiver
  │                                           │
  ├──── File Transfer Start (0x10) ─────────►│
  │                                           │
  │◄──────────── ACK (0x0A) ──────────────────┤
  │                                           │
  ├──── File Chunk 0 (0x11) ────────────────►│
  │◄──────────── ACK (0x0A) ──────────────────┤
  │                                           │
  ├──── File Chunk 1 (0x11) ────────────────►│
  │◄──────────── ACK (0x0A) ──────────────────┤
  │                                           │
  │        ... (more chunks) ...              │
  │                                           │
  ├──── File Transfer Complete (0x12) ──────►│
  │                                           │
  │◄──────────── ACK (0x0A) ──────────────────┤
  │                                           │
```

---

## Error Handling

### Error Types

1. **CRC Mismatch**: Calculated CRC ≠ Received CRC
   - Response: NACK with ERROR = 0x01
   - Action: Sender retries message

2. **Invalid Message Type**: Unknown MSG_TYPE
   - Response: NACK with ERROR = 0x02
   - Action: Sender logs error

3. **Payload Too Large**: LENGTH > 1024
   - Response: NACK with ERROR = 0x03
   - Action: Sender chunks data

4. **Timeout**: No response within 5 seconds
   - Action: Sender retries (max 3 attempts)

### Retry Strategy

```
Attempt 1: Wait 1 second
Attempt 2: Wait 2 seconds
Attempt 3: Wait 5 seconds
After 3 failures: Log error and abort
```

---

## Performance Characteristics

### Throughput

| Baud Rate | Theoretical | Practical | Overhead |
|-----------|-------------|-----------|----------|
| 115200 | 14.4 KB/s | ~11 KB/s | ~24% |

**Overhead includes:**
- 7 bytes framing per message
- ACK/NACK responses
- Processing delays

### Latency

| Message Type | Typical Latency |
|--------------|-----------------|
| Keypress | 10-20 ms |
| Text display | 50-100 ms |
| Image display | 200-500 ms |
| File chunk | 100-200 ms |

---

## Implementation Notes

### ESP32 Implementation

```
// Send message
bool sendMessage(uint8_t msgType, const uint8_t* payload, uint16_t length) {
    uint8_t header;
    header = 0xAA;               // START
    header = msgType;             // MSG_TYPE
    header = (length >> 8) & 0xFF; // LENGTH_H
    header = length & 0xFF;        // LENGTH_L
    
    // Calculate CRC over header[1..3] + payload
    uint16_t crc = crc16_ccitt(header + 1, 3);
    crc = crc16_ccitt_continue(crc, payload, length);
    
    // Send frame
    Serial2.write(header, 4);
    Serial2.write(payload, length);
    Serial2.write((crc >> 8) & 0xFF);
    Serial2.write(crc & 0xFF);
    
    return waitForAck(msgType, 5000);
}
```

### Raspberry Pi Implementation

```
def receive_message():
    # Wait for START byte
    while True:
        byte = uart.read(1)
        if byte == b'\xAA':
            break
    
    # Read header
    msg_type = uart.read(1)
    length_h = uart.read(1)
    length_l = uart.read(1)
    length = (length_h << 8) | length_l
    
    # Read payload
    payload = uart.read(length)
    
    # Read CRC
    crc_h = uart.read(1)
    crc_l = uart.read(1)
    received_crc = (crc_h << 8) | crc_l
    
    # Verify CRC
    data = bytes([msg_type, length_h, length_l]) + payload
    calculated_crc = crc16_ccitt(data)
    
    if calculated_crc != received_crc:
        send_nack(msg_type, ERROR_CRC)
        return None
    
    send_ack(msg_type)
    return (msg_type, payload)
```

---

## Testing

### Test Cases

1. **Basic Transmission**: Send/receive all message types
2. **CRC Validation**: Inject CRC errors, verify NACK
3. **Large Payloads**: Test max payload size (1024 bytes)
4. **High Throughput**: Continuous message stream
5. **Error Recovery**: Simulate timeouts and retries
6. **Concurrent Messages**: Multiple messages in flight

### Debug Mode

Enable verbose logging:
```
#define UART_DEBUG 1  // ESP32
DEBUG_UART = True      # Python
```

---

**Version**: 1.0  
**Last Updated**: 2025-11-24  
**Status**: Stable
```

