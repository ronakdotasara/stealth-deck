# File 62: docs/software/architecture.md

```markdown
# Stealth Deck - Software Architecture

Complete system architecture documentation.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Communication Protocol](#communication-protocol)
4. [Data Flow](#data-flow)
5. [State Management](#state-management)
6. [Security Architecture](#security-architecture)
7. [Performance Considerations](#performance-considerations)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                         │
│          (Display, Keypad, Visual Feedback)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │      ESP32          │
          │   (UI Controller)   │
          │                     │
          │  - Display Driver   │
          │  - Keypad Scanner   │
          │  - Mode Manager     │
          │  - Local Processing │
          └──────────┬──────────┘
                     │
                UART │ 115200 baud
              Binary │ Protocol
                     │ CRC16
                     │
          ┌──────────▼──────────┐
          │   Raspberry Pi      │
          │  (AI Processor)     │
          │                     │
          │  - Gemini Client    │
          │  - Camera Control   │
          │  - Security Manager │
          │  - Feature Modules  │
          └──────────┬──────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
  ┌─────▼─────┐            ┌─────▼─────┐
  │  Camera   │            │  Network  │
  │  Module   │            │  Services │
  └───────────┘            └───────────┘
```

---

## Component Architecture

### ESP32 Firmware Architecture

```
┌──────────────────────────────────────────────────┐
│                    ESP32                         │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │         Application Layer                  │ │
│  │  - Mode Management (Calculator/Smart)      │ │
│  │  - State Machine                           │ │
│  │  - User Input Processing                   │ │
│  └────────────────────────────────────────────┘ │
│                       │                          │
│  ┌────────────────────┼────────────────────────┐│
│  │         Hardware Abstraction Layer         ││
│  │                                             ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │ Display  │  │ Keypad   │  │  UART    │ ││
│  │  │  Driver  │  │  Driver  │  │ Protocol │ ││
│  │  └──────────┘  └──────────┘  └──────────┘ ││
│  │                                             ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │Bluetooth │  │   WiFi   │  │   CRC    │ ││
│  │  │   SPP    │  │ Sniffer  │  │  Utils   │ ││
│  │  └──────────┘  └──────────┘  └──────────┘ ││
│  └─────────────────────────────────────────────┘│
│                       │                          │
│  ┌────────────────────▼────────────────────────┐│
│  │         Arduino/ESP-IDF Framework          ││
│  │  - FreeRTOS                                ││
│  │  - Hardware Peripherals                   ││
│  │  - Network Stack                          ││
│  └───────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

### Raspberry Pi Application Architecture

```
┌──────────────────────────────────────────────────┐
│              Raspberry Pi Zero 2W                │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │         Application Layer                  │ │
│  │  - Main Service Daemon                     │ │
│  │  - Request Router                          │ │
│  │  - Response Handler                        │ │
│  └────────────────────────────────────────────┘ │
│                       │                          │
│  ┌────────────────────┼────────────────────────┐│
│  │         Business Logic Layer               ││
│  │                                             ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │  Gemini  │  │  Notes   │  │Clipboard │ ││
│  │  │  Client  │  │ Manager  │  │ Manager  │ ││
│  │  └──────────┘  └──────────┘  └──────────┘ ││
│  │                                             ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │  Search  │  │   P2P    │  │ Security │ ││
│  │  │  Engine  │  │ Manager  │  │ Manager  │ ││
│  │  └──────────┘  └──────────┘  └──────────┘ ││
│  └─────────────────────────────────────────────┘│
│                       │                          │
│  ┌────────────────────┼────────────────────────┐│
│  │         Infrastructure Layer               ││
│  │                                             ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │   UART   │  │  Camera  │  │ Bluetooth│ ││
│  │  │ Handler  │  │Controller│  │ Manager  │ ││
│  │  └──────────┘  └──────────┘  └──────────┘ ││
│  │                                             ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │  Config  │  │  Logger  │  │  Memory  │ ││
│  │  │ Manager  │  │          │  │ Monitor  │ ││
│  │  └──────────┘  └──────────┘  └──────────┘ ││
│  └─────────────────────────────────────────────┘│
│                       │                          │
│  ┌────────────────────▼────────────────────────┐│
│  │         Operating System Layer             ││
│  │  - Raspberry Pi OS (Linux)                 ││
│  │  - Python Runtime                          ││
│  │  - System Services                         ││
│  └───────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

---

## Communication Protocol

### UART Protocol Stack

```
┌─────────────────────────────────────────┐
│        Application Messages             │
│  (Text, Image Data, Commands)           │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Message Protocol Layer          │
│  - Message Type                         │
│  - Payload Length                       │
│  - Sequence Numbers                     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Framing Layer                   │
│  - Start Marker (0xAA)                  │
│  - Length Fields                        │
│  - CRC16 Checksum                       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Physical Layer                  │
│  - UART (115200 baud, 8N1)              │
│  - GPIO14/15 (Pi) ↔ GPIO16/17 (ESP32)   │
└─────────────────────────────────────────┘
```

### Message Format

```
Byte:  0      1         2         3      4..N     N+1    N+2
     ┌─────┬────────┬────────┬────────┬────────┬──────┬──────┐
     │START│MSG_TYPE│LENGTH_H│LENGTH_L│PAYLOAD │CRC_H │CRC_L │
     │0xAA │        │        │        │        │      │      │
     └─────┴────────┴────────┴────────┴────────┴──────┴──────┘

START:    0xAA (170 decimal)
MSG_TYPE: Message type identifier
LENGTH:   Payload length (16-bit, big-endian)
PAYLOAD:  Message data (0-1024 bytes)
CRC:      CRC16-CCITT checksum (16-bit, big-endian)
```

---

## Data Flow

### Text Query Flow

```
User Input → Keypad → ESP32 → UART → Pi → Gemini API
                ↓                            ↓
            Display ← ← ← ← ← ← UART ← ← Response
```

**Step-by-Step:**

1. User enters query via T9 keypad (ESP32)
2. ESP32 builds text string
3. User presses submit (#)
4. ESP32 sends `MSG_DISPLAY_TEXT` via UART
5. Pi receives and validates message (CRC16)
6. Pi sends ACK back to ESP32
7. Pi calls Gemini API with query
8. Gemini processes and returns response
9. Pi formats response for display
10. Pi sends response via UART to ESP32
11. ESP32 receives and validates
12. ESP32 renders text on display
13. User sees response

### Image Analysis Flow

```
User → Camera → Pi → Compress → Gemini API
                                     ↓
Display ← ESP32 ← UART ← Pi ← Response
```

**Step-by-Step:**

1. User presses camera button (ESP32)
2. ESP32 sends `MSG_CAMERA_CAPTURE` to Pi
3. Pi captures image via camera module
4. Pi compresses/resizes image
5. Pi sends to Gemini Vision API
6. Gemini analyzes image
7. Pi formats analysis result
8. Pi sends result to ESP32 via UART
9. ESP32 displays analysis

---

## State Management

### ESP32 State Machine

```
                 ┌─────────────┐
                 │   STARTUP   │
                 └──────┬──────┘
                        │
                 ┌──────▼──────┐
            ┌────│  CALCULATOR │◄────┐
            │    │    MODE     │     │
            │    └──────┬──────┘     │
            │           │            │
            │     [FN+5+5+5]         │
            │           │            │
            │    ┌──────▼──────┐     │
            │    │    SMART    │     │
            │    │    MODE     │     │
            │    └──────┬──────┘     │
            │           │            │
            │     [FN+FIX]           │
            │           │            │
            └───────────▼────────────┘
                 ┌──────────────┐
                 │  PANIC MODE  │
                 └──────────────┘
```

### Raspberry Pi State Management

```
class StateManager:
    states = {
        'idle': Handle idle state
        'processing': Handle AI processing
        'camera': Handle camera operation
        'transfer': Handle P2P transfer
        'locked': Handle locked state
        'panic': Handle panic mode
    }
    
    transitions = {
        'idle' → 'processing': Query received
        'processing' → 'idle': Response sent
        'idle' → 'camera': Camera request
        'camera' → 'processing': Image captured
        '*' → 'panic': Panic signal
        'panic' → 'locked': Panic complete
    }
```

---

## Security Architecture

### Security Layers

```
┌──────────────────────────────────────────────┐
│         Application Security                 │
│  - Panic Mode                                │
│  - Screen Lock                               │
│  - Fake History                              │
└────────────────┬─────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────┐
│         Data Security                        │
│  - AES-256-GCM Encryption                    │
│  - Secure Deletion                           │
│  - Key Management                            │
└────────────────┬─────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────┐
│         Communication Security               │
│  - CRC16 Integrity                           │
│  - Message Validation                        │
│  - P2P Encryption                            │
└────────────────┬─────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────┐
│         Physical Security                    │
│  - Secure Boot (optional)                    │
│  - Write Protection                          │
│  - Anti-Tamper                               │
└──────────────────────────────────────────────┘
```

### Encryption Key Hierarchy

```
Master Key (32 bytes)
    │
    ├─► Notes Encryption Key
    │       └─► Individual Note Keys (derived)
    │
    ├─► Clipboard Encryption Key
    │
    ├─► P2P Session Keys (ephemeral)
    │
    └─► Config Encryption Key
```

---

## Performance Considerations

### ESP32 Optimization

**Memory Management:**
- Stack size: 4KB per task
- Heap: ~200KB available
- Buffer pools for UART
- String pooling for UI

**CPU Optimization:**
- Dual-core utilization
- Core 0: Arduino loop, UI
- Core 1: WiFi/Bluetooth
- FreeRTOS task priorities

**Power Management:**
- Light sleep: 30s idle
- Deep sleep: 60s idle
- CPU frequency scaling
- Peripheral power down

### Raspberry Pi Optimization

**Memory Management:**
- Python GC tuning
- Object pooling
- Image buffer reuse
- Cache size limits

**CPU Optimization:**
- Multi-threading for I/O
- Async operations
- Response caching
- Governor: ondemand

**I/O Optimization:**
- UART buffering
- Non-blocking reads
- Batch processing
- Rate limiting

---

## Design Patterns

### Used Patterns

1. **State Pattern**: Mode management
2. **Observer Pattern**: Event callbacks
3. **Factory Pattern**: Message creation
4. **Singleton Pattern**: Managers
5. **Strategy Pattern**: Rendering strategies
6. **Command Pattern**: User actions
7. **Template Method**: Protocol handling

---

## Thread Model

### ESP32 Tasks

```
Priority 10: UI Rendering (Core 0)
Priority 5:  UART Handler (Core 0)
Priority 3:  Keypad Scanner (Core 0)
Priority 2:  Bluetooth (Core 1)
Priority 1:  WiFi (Core 1)
```

### Raspberry Pi Threads

```
Main Thread:     Event loop
UART Thread:     Serial I/O
Camera Thread:   Image capture
Worker Thread:   AI processing
Monitor Thread:  System monitoring
```

---

## Error Handling Strategy

### Levels of Error Handling

1. **Graceful Degradation**: Feature fails, app continues
2. **Retry Logic**: Transient failures (network, etc.)
3. **User Notification**: Clear error messages
4. **Logging**: All errors logged
5. **Recovery**: Automatic recovery when possible
6. **Panic Mode**: Catastrophic failure → lockdown

---

**Version**: 1.0  
**Last Updated**: 2025-11-24
```

