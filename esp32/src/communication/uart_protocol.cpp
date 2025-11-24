/**
 * ============================================================================
 * @file uart_protocol.cpp
 * @brief UART Communication Protocol Implementation
 * @version 1.0.0
 * @date 2025-11-24
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Complete implementation of the UART protocol including:
 * 
 * - Frame parsing state machine
 * - CRC16-CCITT checksum calculation
 * - Message queue management
 * - ACK/NACK handling
 * - Automatic retry mechanism
 * - Throughput calculation
 * - Error detection and recovery
 * 
 * ============================================================================
 * PARSER STATE MACHINE:
 * 
 *     IDLE ──[0xAA]──> START ──[type]──> TYPE ──[len_h]──> LENGTH_H
 *                                                               │
 *                                                               ▼
 *     CRC_L <──[crc_l]── CRC_H <──[crc_h]── PAYLOAD <──[len_l]─ LENGTH_L
 *       │                                      │
 *       │                                      │ (read N bytes)
 *       │                                      │
 *       └──────> [Verify CRC] ──> [Handle Message]
 * 
 * ============================================================================
 * CRC16-CCITT CALCULATION:
 * 
 * Polynomial: x^16 + x^12 + x^5 + 1 (0x1021)
 * Initial value: 0xFFFF
 * Final XOR: 0x0000
 * 
 * Used for error detection in transmitted data.
 * 
 * ============================================================================
 */

#include "uart_protocol.h"

// Debug logging
#ifdef DEBUG
  #define UART_DEBUG(x) DEBUG_SERIAL.print("[UART] "); DEBUG_SERIAL.println(x)
  #define UART_DEBUGF(format, ...) DEBUG_SERIAL.printf("[UART] " format "\n", __VA_ARGS__)
#else
  #define UART_DEBUG(x)
  #define UART_DEBUGF(format, ...)
#endif

// ============================================================================
// CRC16-CCITT LOOKUP TABLE (for speed)
// ============================================================================

static const uint16_t crc16_ccitt_table[256] = {
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
    0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
    0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
    0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
    0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
    0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
    0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
    0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
    0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
    0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
    0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
    0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
    0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
    0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
    0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
    0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
    0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
    0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
    0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
    0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
    0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
    0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
    0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
};

// ============================================================================
// CONSTRUCTOR
// ============================================================================

/**
 * @brief Constructor - Initialize member variables
 */
UARTProtocol::UARTProtocol() :
    _serial(nullptr),
    _rxPin(-1),
    _txPin(-1),
    _baudRate(115200),
    _initialized(false),
    _parserState(PARSER_STATE_IDLE),
    _currentType(0),
    _currentLength(0),
    _payloadIndex(0),
    _expectedCrc(0),
    _receivedCrc(0),
    _rxQueueHead(0),
    _rxQueueTail(0),
    _txPendingHead(0),
    _txPendingTail(0),
    _txSequence(0),
    _lastRxSequence(0),
    _lastHeartbeatTime(0),
    _lastRxTime(0),
    _lastStatsTime(0),
    _statsBytes(0),
    _lastError(ERR_NONE),
    _consecutiveErrors(0)
{
    memset(_currentPayload, 0, UART_MAX_PAYLOAD_SIZE);
}

// ============================================================================
// DESTRUCTOR
// ============================================================================

/**
 * @brief Destructor
 */
UARTProtocol::~UARTProtocol() {
    end();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * @brief Initialize UART communication
 * 
 * @param rxPin RX pin number
 * @param txPin TX pin number
 * @param baudRate Baud rate
 * @return true if successful
 */
bool UARTProtocol::begin(int rxPin, int txPin, uint32_t baudRate) {
    UART_DEBUG("Initializing UART...");
    
    _rxPin = rxPin;
    _txPin = txPin;
    _baudRate = baudRate;
    
    // Use Serial2 for ESP32
    _serial = &Serial2;
    
    // Initialize serial port
    _serial->begin(_baudRate, SERIAL_8N1, _rxPin, _txPin);
    _serial->setRxBufferSize(UART_RX_BUFFER_SIZE);
    _serial->setTxBufferSize(UART_TX_BUFFER_SIZE);
    
    // Wait for serial to stabilize
    delay(100);
    
    // Clear buffers
    while (_serial->available()) {
        _serial->read();
    }
    
    // Reset state
    resetParser();
    clearQueue();
    resetStats();
    
    _initialized = true;
    _lastHeartbeatTime = millis();
    _lastRxTime = millis();
    _lastStatsTime = millis();
    
    UART_DEBUGF("✓ UART initialized (RX=%d, TX=%d, %d baud)", 
                _rxPin, _txPin, _baudRate);
    
    return true;
}

/**
 * @brief Stop UART communication
 */
void UARTProtocol::end() {
    if (_serial) {
        _serial->end();
        _serial = nullptr;
    }
    
    _initialized = false;
    
    UART_DEBUG("UART stopped");
}

/**
 * @brief Check if connected to Pi
 * 
 * @return true if received heartbeat within last 10 seconds
 */
bool UARTProtocol::isConnected() const {
    unsigned long now = millis();
    return (now - _lastHeartbeatTime < 10000);
}

// ============================================================================
// MESSAGE SENDING - HIGH-LEVEL API
// ============================================================================

/**
 * @brief Send keypress event
 */
bool UARTProtocol::sendKeypress(uint8_t key, uint8_t eventType) {
    uint8_t payload[2];
    payload[0] = key;
    payload[1] = eventType;
    
    bool result = send(MSG_TYPE_KEYPRESS, payload, 2, false);
    
    if (result) {
        UART_DEBUGF("Sent keypress: 0x%02X type=%d", key, eventType);
    }
    
    return result;
}

/**
 * @brief Send camera capture command
 */
bool UARTProtocol::sendCameraCapture() {
    bool result = send(MSG_TYPE_CAMERA_CAPTURE, nullptr, 0, true);
    
    if (result) {
        UART_DEBUG("Sent camera capture command");
    }
    
    return result;
}

/**
 * @brief Send panic signal
 */
bool UARTProtocol::sendPanic() {
    bool result = send(MSG_TYPE_PANIC, nullptr, 0, false);
    
    if (result) {
        UART_DEBUG("Sent PANIC signal");
    }
    
    return result;
}

/**
 * @brief Send heartbeat
 */
bool UARTProtocol::sendHeartbeat() {
    uint32_t uptime = millis();
    uint8_t payload[4];
    payload[0] = (uptime >> 24) & 0xFF;
    payload[1] = (uptime >> 16) & 0xFF;
    payload[2] = (uptime >> 8) & 0xFF;
    payload[3] = uptime & 0xFF;
    
    bool result = send(MSG_TYPE_HEARTBEAT, payload, 4, false);
    
    if (result) {
        UART_DEBUG("Sent heartbeat");
    }
    
    return result;
}

/**
 * @brief Send battery status
 */
bool UARTProtocol::sendBatteryStatus(uint8_t percent, float voltage, bool charging) {
    uint8_t payload[4];
    uint16_t voltageMillivolts = (uint16_t)(voltage * 1000.0f);
    
    payload[0] = percent;
    payload[1] = (voltageMillivolts >> 8) & 0xFF;
    payload[2] = voltageMillivolts & 0xFF;
    payload[3] = charging ? 1 : 0;
    
    bool result = send(MSG_TYPE_BATTERY_STATUS, payload, 4, false);
    
    if (result) {
        UART_DEBUGF("Sent battery status: %d%% %.2fV %s", 
                    percent, voltage, charging ? "CHARGING" : "");
    }
    
    return result;
}

/**
 * @brief Send mode change notification
 */
bool UARTProtocol::sendModeChange(uint8_t mode) {
    uint8_t payload[1];
    payload[0] = mode;
    
    bool result = send(MSG_TYPE_MODE_CHANGE, payload, 1, false);
    
    if (result) {
        UART_DEBUGF("Sent mode change: %d", mode);
    }
    
    return result;
}

/**
 * @brief Send ACK
 */
bool UARTProtocol::sendAck(uint8_t sequence) {
    uint8_t payload[1];
    payload[0] = sequence;
    
    bool result = send(MSG_TYPE_ACK, payload, 1, false);
    
    if (result) {
        _stats.acksSent++;
        UART_DEBUGF("Sent ACK for seq=%d", sequence);
    }
    
    return result;
}

/**
 * @brief Send NACK
 */
bool UARTProtocol::sendNack(uint8_t sequence) {
    uint8_t payload[1];
    payload[0] = sequence;
    
    bool result = send(MSG_TYPE_NACK, payload, 1, false);
    
    if (result) {
        _stats.nacksSent++;
        UART_DEBUGF("Sent NACK for seq=%d", sequence);
    }
    
    return result;
}

// ============================================================================
// MESSAGE SENDING - LOW-LEVEL API
// ============================================================================

/**
 * @brief Send raw message
 */
bool UARTProtocol::send(uint8_t type, const uint8_t* payload, uint16_t length, bool needsAck) {
    if (!_initialized || !_serial) {
        _lastError = ERR_UART_TIMEOUT;
        return false;
    }
    
    if (length > UART_MAX_PAYLOAD_SIZE) {
        UART_DEBUGF("ERROR: Payload too large (%d > %d)", length, UART_MAX_PAYLOAD_SIZE);
        return false;
    }
    
    // Send frame
    bool result = sendFrame(type, payload, length);
    
    if (result) {
        _stats.messagesSent++;
        _stats.bytesTransferred += length + 7;  // Include overhead
        
        // If ACK is needed, add to pending queue
        if (needsAck) {
            UARTMessage msg;
            msg.type = type;
            msg.length = length;
            if (payload && length > 0) {
                memcpy(msg.payload, payload, length);
            }
            msg.sequence = _txSequence;
            msg.timestamp = millis();
            msg.needsAck = true;
            msg.retryCount = 0;
            
            addToPendingQueue(msg);
        }
    }
    
    return result;
}

/**
 * @brief Send message with automatic retry
 */
bool UARTProtocol::sendWithRetry(UARTMessage& msg) {
    msg.retryCount = 0;
    
    while (msg.retryCount < UART_RETRY_COUNT) {
        if (send(msg.type, msg.payload, msg.length, true)) {
            // Wait for ACK
            unsigned long startTime = millis();
            
            while (millis() - startTime < UART_TIMEOUT_MS) {
                process();
                
                // Check if ACK received (message removed from pending queue)
                bool found = false;
                for (uint8_t i = _txPendingTail; i != _txPendingHead; 
                     i = (i + 1) % UART_MESSAGE_QUEUE_SIZE) {
                    if (_txPendingQueue[i].sequence == msg.sequence) {
                        found = true;
                        break;
                    }
                }
                
                if (!found) {
                    // ACK received!
                    return true;
                }
                
                delay(1);
            }
            
            // Timeout
            _stats.timeouts++;
            msg.retryCount++;
            _stats.retries++;
            
            UART_DEBUGF("Timeout waiting for ACK (retry %d/%d)", 
                        msg.retryCount, UART_RETRY_COUNT);
        } else {
            return false;
        }
    }
    
    UART_DEBUG("ERROR: Max retries exceeded");
    return false;
}

// ============================================================================
// MESSAGE RECEIVING
// ============================================================================

/**
 * @brief Read next message from queue
 */
UARTMessage UARTProtocol::read() {
    if (!available()) {
        return UARTMessage();
    }
    
    UARTMessage msg = _rxQueue[_rxQueueTail];
    _rxQueueTail = (_rxQueueTail + 1) % UART_MESSAGE_QUEUE_SIZE;
    
    return msg;
}

/**
 * @brief Peek at next message
 */
UARTMessage UARTProtocol::peek() const {
    if (!available()) {
        return UARTMessage();
    }
    
    return _rxQueue[_rxQueueTail];
}

/**
 * @brief Get message count
 */
uint8_t UARTProtocol::getMessageCount() const {
    if (_rxQueueHead >= _rxQueueTail) {
        return _rxQueueHead - _rxQueueTail;
    } else {
        return UART_MESSAGE_QUEUE_SIZE - _rxQueueTail + _rxQueueHead;
    }
}

/**
 * @brief Clear receive queue
 */
void UARTProtocol::clearQueue() {
    _rxQueueHead = 0;
    _rxQueueTail = 0;
}

// ============================================================================
// PROCESSING
// ============================================================================

/**
 * @brief Process incoming UART data
 */
void UARTProtocol::process() {
    if (!_initialized || !_serial) {
        return;
    }
    
    // Process all available bytes
    while (_serial->available()) {
        uint8_t byte = _serial->read();
        parseByte(byte);
        _lastRxTime = millis();
    }
    
    // Process retries
    processRetries();
    
    // Update throughput
    updateThroughput();
}

/**
 * @brief Process pending ACKs and retries
 */
void UARTProtocol::processRetries() {
    unsigned long now = millis();
    
    // Check pending messages for timeout
    for (uint8_t i = _txPendingTail; i != _txPendingHead; 
         i = (i + 1) % UART_MESSAGE_QUEUE_SIZE) {
        
        UARTMessage& msg = _txPendingQueue[i];
        
        if (now - msg.timestamp >= UART_TIMEOUT_MS) {
            // Timeout - retry
            if (msg.retryCount < UART_RETRY_COUNT) {
                msg.retryCount++;
                msg.timestamp = now;
                _stats.retries++;
                
                UART_DEBUGF("Retrying message type=0x%02X (attempt %d/%d)", 
                            msg.type, msg.retryCount, UART_RETRY_COUNT);
                
                sendFrame(msg.type, msg.payload, msg.length);
            } else {
                // Max retries exceeded - remove from queue
                UART_DEBUGF("Max retries exceeded for message type=0x%02X", msg.type);
                removeFromPendingQueue(msg.sequence);
                _stats.timeouts++;
            }
        }
    }
}

// ============================================================================
// PARSER
// ============================================================================

/**
 * @brief Parse incoming byte through state machine
 */
void UARTProtocol::parseByte(uint8_t byte) {
    switch (_parserState) {
        
        // ====================================================================
        // IDLE - Waiting for start byte
        // ====================================================================
        case PARSER_STATE_IDLE:
            if (byte == UART_START_BYTE) {
                _parserState = PARSER_STATE_TYPE;
            }
            break;
        
        // ====================================================================
        // TYPE - Read message type
        // ====================================================================
        case PARSER_STATE_TYPE:
            _currentType = byte;
            _parserState = PARSER_STATE_LENGTH_H;
            break;
        
        // ====================================================================
        // LENGTH_H - Read length high byte
        // ====================================================================
        case PARSER_STATE_LENGTH_H:
            _currentLength = (uint16_t)byte << 8;
            _parserState = PARSER_STATE_LENGTH_L;
            break;
        
        // ====================================================================
        // LENGTH_L - Read length low byte
        // ====================================================================
        case PARSER_STATE_LENGTH_L:
            _currentLength |= byte;
            
            // Validate length
            if (_currentLength > UART_MAX_PAYLOAD_SIZE) {
                UART_DEBUGF("ERROR: Invalid payload length %d", _currentLength);
                resetParser();
                break;
            }
            
            _payloadIndex = 0;
            
            if (_currentLength == 0) {
                // No payload - go to CRC
                _parserState = PARSER_STATE_CRC_H;
            } else {
                _parserState = PARSER_STATE_PAYLOAD;
            }
            break;
        
        // ====================================================================
        // PAYLOAD - Read payload bytes
        // ====================================================================
        case PARSER_STATE_PAYLOAD:
            _currentPayload[_payloadIndex++] = byte;
            
            if (_payloadIndex >= _currentLength) {
                _parserState = PARSER_STATE_CRC_H;
            }
            break;
        
        // ====================================================================
        // CRC_H - Read CRC high byte
        // ====================================================================
        case PARSER_STATE_CRC_H:
            _receivedCrc = (uint16_t)byte << 8;
            _parserState = PARSER_STATE_CRC_L;
            break;
        
        // ====================================================================
        // CRC_L - Read CRC low byte and verify
        // ====================================================================
        case PARSER_STATE_CRC_L:
            _receivedCrc |= byte;
            
            // Verify CRC
            if (verifyCrc16(_currentType, _currentLength, _currentPayload, _receivedCrc)) {
                // CRC valid - create message
                UARTMessage msg;
                msg.type = _currentType;
                msg.length = _currentLength;
                memcpy(msg.payload, _currentPayload, _currentLength);
                msg.timestamp = millis();
                
                // Handle message
                handleReceivedMessage(msg);
                
                _stats.messagesReceived++;
                _consecutiveErrors = 0;
            } else {
                // CRC error
                UART_DEBUGF("ERROR: CRC mismatch (expected 0x%04X, got 0x%04X)", 
                            _expectedCrc, _receivedCrc);
                _stats.crcErrors++;
                _consecutiveErrors++;
                
                // Send NACK
                sendNack(_lastRxSequence);
            }
            
            resetParser();
            break;
    }
}

/**
 * @brief Handle received message
 */
void UARTProtocol::handleReceivedMessage(const UARTMessage& msg) {
    UART_DEBUGF("Received message type=0x%02X length=%d", msg.type, msg.length);
    
    // Handle special message types
    switch (msg.type) {
        case MSG_TYPE_HEARTBEAT:
            _lastHeartbeatTime = millis();
            UART_DEBUG("Heartbeat received from Pi");
            break;
        
        case MSG_TYPE_ACK:
            if (msg.length >= 1) {
                uint8_t sequence = msg.payload[0];
                removeFromPendingQueue(sequence);
                _stats.acksReceived++;
                UART_DEBUGF("ACK received for seq=%d", sequence);
            }
            break;
        
        case MSG_TYPE_NACK:
            if (msg.length >= 1) {
                uint8_t sequence = msg.payload[0];
                _stats.nacksReceived++;
                UART_DEBUGF("NACK received for seq=%d", sequence);
                // Retry will be handled by processRetries()
            }
            break;
        
        default:
            // Add to receive queue
            if (!addToRxQueue(msg)) {
                UART_DEBUG("ERROR: RX queue full!");
            }
            break;
    }
}

// ============================================================================
// QUEUE MANAGEMENT
// ============================================================================

/**
 * @brief Add message to receive queue
 */
bool UARTProtocol::addToRxQueue(const UARTMessage& msg) {
    uint8_t nextHead = (_rxQueueHead + 1) % UART_MESSAGE_QUEUE_SIZE;
    
    if (nextHead == _rxQueueTail) {
        return false;  // Queue full
    }
    
    _rxQueue[_rxQueueHead] = msg;
    _rxQueueHead = nextHead;
    
    return true;
}

/**
 * @brief Add message to pending queue
 */
bool UARTProtocol::addToPendingQueue(const UARTMessage& msg) {
    uint8_t nextHead = (_txPendingHead + 1) % UART_MESSAGE_QUEUE_SIZE;
    
    if (nextHead == _txPendingTail) {
        return false;  // Queue full
    }
    
    _txPendingQueue[_txPendingHead] = msg;
    _txPendingHead = nextHead;
    
    return true;
}

/**
 * @brief Remove message from pending queue
 */
void UARTProtocol::removeFromPendingQueue(uint8_t sequence) {
    for (uint8_t i = _txPendingTail; i != _txPendingHead; 
         i = (i + 1) % UART_MESSAGE_QUEUE_SIZE) {
        
        if (_txPendingQueue[i].sequence == sequence) {
            // Found - shift remaining messages
            uint8_t j = i;
            while (j != _txPendingHead) {
                uint8_t next = (j + 1) % UART_MESSAGE_QUEUE_SIZE;
                _txPendingQueue[j] = _txPendingQueue[next];
                j = next;
            }
            
            // Decrease head
            if (_txPendingHead == 0) {
                _txPendingHead = UART_MESSAGE_QUEUE_SIZE - 1;
            } else {
                _txPendingHead--;
            }
            
            return;
        }
    }
}

// ============================================================================
// FRAME SENDING
// ============================================================================

/**
 * @brief Send raw frame
 */
bool UARTProtocol::sendFrame(uint8_t type, const uint8_t* payload, uint16_t length) {
    if (!_serial) {
        return false;
    }
    
    // Build frame in temporary buffer
    uint8_t frame[UART_MAX_FRAME_SIZE];
    uint16_t frameIndex = 0;
    
    // Start byte
    frame[frameIndex++] = UART_START_BYTE;
    
    // Message type
    frame[frameIndex++] = type;
    
    // Length (big-endian)
    frame[frameIndex++] = (length >> 8) & 0xFF;
    frame[frameIndex++] = length & 0xFF;
    
    // Payload
    if (payload && length > 0) {
        memcpy(&frame[frameIndex], payload, length);
        frameIndex += length;
    }
    
    // Calculate CRC16 (over type + length + payload)
    uint16_t crc = calculateCrc16(&frame[1], frameIndex - 1);
    
    // CRC (big-endian)
    frame[frameIndex++] = (crc >> 8) & 0xFF;
    frame[frameIndex++] = crc & 0xFF;
    
    // Send frame
    size_t written = _serial->write(frame, frameIndex);
    _serial->flush();
    
    if (written != frameIndex) {
        UART_DEBUGF("ERROR: Write failed (%d/%d bytes)", written, frameIndex);
        return false;
    }
    
    _statsBytes += written;
    
    return true;
}

// ============================================================================
// CRC CALCULATION
// ============================================================================

/**
 * @brief Calculate CRC16-CCITT
 */
uint16_t UARTProtocol::calculateCrc16(const uint8_t* data, uint16_t length) {
    uint16_t crc = 0xFFFF;
    
    for (uint16_t i = 0; i < length; i++) {
        uint8_t index = (crc >> 8) ^ data[i];
        crc = (crc << 8) ^ crc16_ccitt_table[index];
    }
    
    return crc;
}

/**
 * @brief Verify CRC16
 */
bool UARTProtocol::verifyCrc16(uint8_t type, uint16_t length, 
                               const uint8_t* payload, uint16_t expectedCrc) {
    // Build data for CRC calculation
    uint8_t data[UART_MAX_PAYLOAD_SIZE + 3];
    data[0] = type;
    data[1] = (length >> 8) & 0xFF;
    data[2] = length & 0xFF;
    
    if (payload && length > 0) {
        memcpy(&data[3], payload, length);
    }
    
    _expectedCrc = calculateCrc16(data, length + 3);
    
    return (_expectedCrc == expectedCrc);
}

// ============================================================================
// STATISTICS
// ============================================================================

/**
 * @brief Reset statistics
 */
void UARTProtocol::resetStats() {
    _stats.messagesSent = 0;
    _stats.messagesReceived = 0;
    _stats.bytesTransferred = 0;
    _stats.crcErrors = 0;
    _stats.timeouts = 0;
    _stats.retries = 0;
    _stats.acksSent = 0;
    _stats.acksReceived = 0;
    _stats.nacksSent = 0;
    _stats.nacksReceived = 0;
    _stats.throughput = 0.0f;
    
    _statsBytes = 0;
    _lastStatsTime = millis();
}

/**
 * @brief Update throughput calculation
 */
void UARTProtocol::updateThroughput() {
    unsigned long now = millis();
    unsigned long elapsed = now - _lastStatsTime;
    
    if (elapsed >= 1000) {  // Update every second
        _stats.throughput = (_statsBytes * 1000.0f) / elapsed;
        _statsBytes = 0;
        _lastStatsTime = now;
    }
}

/**
 * @brief Print statistics
 */
void UARTProtocol::printStats() const {
    #ifdef DEBUG
    DEBUG_SERIAL.println("\n===== UART STATISTICS =====");
    DEBUG_SERIAL.printf("Messages Sent: %lu\n", _stats.messagesSent);
    DEBUG_SERIAL.printf("Messages Received: %lu\n", _stats.messagesReceived);
    DEBUG_SERIAL.printf("Bytes Transferred: %lu\n", _stats.bytesTransferred);
    DEBUG_SERIAL.printf("CRC Errors: %lu\n", _stats.crcErrors);
    DEBUG_SERIAL.printf("Timeouts: %lu\n", _stats.timeouts);
    DEBUG_SERIAL.printf("Retries: %lu\n", _stats.retries);
    DEBUG_SERIAL.printf("ACKs: %lu sent, %lu received\n", _stats.acksSent, _stats.acksReceived);
    DEBUG_SERIAL.printf("NACKs: %lu sent, %lu received\n", _stats.nacksSent, _stats.nacksReceived);
    DEBUG_SERIAL.printf("Throughput: %.1f bytes/sec\n", _stats.throughput);
    DEBUG_SERIAL.printf("Connected: %s\n", isConnected() ? "YES" : "NO");
    DEBUG_SERIAL.printf("Messages in Queue: %d\n", getMessageCount());
    DEBUG_SERIAL.println("===========================\n");
    #endif
}

/**
 * @brief Reset parser state
 */
void UARTProtocol::resetParser() {
    _parserState = PARSER_STATE_IDLE;
    _currentType = 0;
    _currentLength = 0;
    _payloadIndex = 0;
    _expectedCrc = 0;
    _receivedCrc = 0;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * @brief Get message type name
 */
const char* getMessageTypeName(uint8_t type) {
    switch (type) {
        case MSG_TYPE_DISPLAY_TEXT: return "DISPLAY_TEXT";
        case MSG_TYPE_DISPLAY_IMAGE: return "DISPLAY_IMAGE";
        case MSG_TYPE_KEYPRESS: return "KEYPRESS";
        case MSG_TYPE_CAMERA_CAPTURE: return "CAMERA_CAPTURE";
        case MSG_TYPE_MODE_CHANGE: return "MODE_CHANGE";
        case MSG_TYPE_PANIC: return "PANIC";
        case MSG_TYPE_HEARTBEAT: return "HEARTBEAT";
        case MSG_TYPE_BATTERY_STATUS: return "BATTERY_STATUS";
        case MSG_TYPE_P2P_DATA: return "P2P_DATA";
        case MSG_TYPE_ACK: return "ACK";
        case MSG_TYPE_NACK: return "NACK";
        default: return "UNKNOWN";
    }
}

/**
 * @brief Dump message contents
 */
void dumpMessage(const UARTMessage& msg) {
    #ifdef DEBUG
    DEBUG_SERIAL.printf("\n--- Message Dump ---\n");
    DEBUG_SERIAL.printf("Type: 0x%02X (%s)\n", msg.type, getMessageTypeName(msg.type));
    DEBUG_SERIAL.printf("Length: %d bytes\n", msg.length);
    DEBUG_SERIAL.printf("Sequence: %d\n", msg.sequence);
    DEBUG_SERIAL.printf("Timestamp: %lu\n", msg.timestamp);
    
    if (msg.length > 0) {
        DEBUG_SERIAL.print("Payload: ");
        for (uint16_t i = 0; i < msg.length && i < 32; i++) {
            DEBUG_SERIAL.printf("%02X ", msg.payload[i]);
        }
        if (msg.length > 32) {
            DEBUG_SERIAL.print("...");
        }
        DEBUG_SERIAL.println();
    }
    
    DEBUG_SERIAL.println("--------------------\n");
    #endif
}

// ============================================================================
// END OF FILE
// ============================================================================
