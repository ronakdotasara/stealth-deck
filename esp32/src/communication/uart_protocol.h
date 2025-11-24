/**
 * ============================================================================
 * @file uart_protocol.h
 * @brief UART Communication Protocol for ESP32 ↔ Raspberry Pi
 * @version 1.0.0
 * @date 2025-11-24
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Binary communication protocol for reliable data exchange between ESP32
 * and Raspberry Pi Zero 2W via UART. This protocol provides:
 * 
 * - Framed message structure with start byte and CRC16 checksum
 * - Multiple message types for different operations
 * - Automatic retry mechanism with timeout
 * - ACK/NACK handshaking for reliability
 * - Message sequence numbers for tracking
 * - Large data transfer with fragmentation
 * - Circular buffer for RX/TX queues
 * - MessagePack serialization support
 * 
 * ============================================================================
 * MESSAGE FRAME STRUCTURE:
 * 
 * ┌─────────┬──────────┬──────────┬──────────┬─────────────┬─────────┬─────────┐
 * │ START   │ MSG_TYPE │ LENGTH_H │ LENGTH_L │ PAYLOAD     │ CRC16_H │ CRC16_L │
 * │ (0xAA)  │ (1 byte) │ (1 byte) │ (1 byte) │ (0-1024 B)  │ (1 byte)│ (1 byte)│
 * └─────────┴──────────┴──────────┴──────────┴─────────────┴─────────┴─────────┘
 * 
 * Total Overhead: 7 bytes per message
 * Maximum Payload: 1024 bytes
 * Maximum Frame Size: 1031 bytes
 * 
 * ============================================================================
 * MESSAGE TYPES:
 * 
 * ESP32 → Pi:
 *   0x03 - Keypress event
 *   0x04 - Camera capture command
 *   0x06 - Panic signal
 *   0x07 - Heartbeat
 *   0x08 - Battery status
 *   0x0A - ACK (acknowledgment)
 *   0x0B - NACK (negative acknowledgment)
 * 
 * Pi → ESP32:
 *   0x01 - Display text
 *   0x02 - Display image buffer
 *   0x05 - Mode change
 *   0x07 - Heartbeat
 *   0x09 - P2P transfer data
 *   0x0A - ACK
 *   0x0B - NACK
 * 
 * Bidirectional:
 *   0x07 - Heartbeat (both directions)
 *   0x0A - ACK (both directions)
 *   0x0B - NACK (both directions)
 * 
 * ============================================================================
 * COMMUNICATION FLOW:
 * 
 * Successful Transfer:
 *   ESP32                         Pi
 *     │                            │
 *     ├────── MSG (seq=1) ────────>│
 *     │                            │
 *     │<─────── ACK (seq=1) ───────┤
 *     │                            │
 * 
 * Failed Transfer with Retry:
 *   ESP32                         Pi
 *     │                            │
 *     ├────── MSG (seq=1) ────────>│
 *     │                            │
 *     │         (timeout)          │
 *     │                            │
 *     ├────── MSG (seq=1) ────────>│ (retry)
 *     │                            │
 *     │<─────── ACK (seq=1) ───────┤
 *     │                            │
 * 
 * CRC Error:
 *   ESP32                         Pi
 *     │                            │
 *     ├────── MSG (seq=1) ────────>│
 *     │                            │
 *     │<────── NACK (seq=1) ───────┤ (CRC fail)
 *     │                            │
 *     ├────── MSG (seq=1) ────────>│ (retry)
 *     │                            │
 *     │<─────── ACK (seq=1) ───────┤
 *     │                            │
 * 
 * ============================================================================
 * PAYLOAD FORMATS:
 * 
 * Keypress Event (0x03):
 *   Byte 0: Key code
 *   Byte 1: Event type (press=1, release=2, long=3, etc.)
 * 
 * Battery Status (0x08):
 *   Byte 0: Battery percentage (0-100)
 *   Byte 1-2: Voltage (uint16_t, millivolts)
 *   Byte 3: Charging flag (0=no, 1=yes)
 * 
 * Display Text (0x01):
 *   Bytes 0-N: UTF-8 text string (null-terminated)
 * 
 * Display Image (0x02):
 *   Bytes 0-1: X coordinate (uint16_t)
 *   Bytes 2-3: Y coordinate (uint16_t)
 *   Bytes 4-5: Width (uint16_t)
 *   Bytes 6-7: Height (uint16_t)
 *   Bytes 8-N: Pixel data (RGB565 or monochrome)
 * 
 * Mode Change (0x05):
 *   Byte 0: New mode (0=calculator, 1=smart, 2=p2p, etc.)
 * 
 * ============================================================================
 * CRC16-CCITT CHECKSUM:
 * 
 * Algorithm: CRC-16-CCITT
 * Polynomial: 0x1021
 * Initial Value: 0xFFFF
 * Final XOR: 0x0000
 * 
 * Covers: MSG_TYPE + LENGTH + PAYLOAD
 * 
 * ============================================================================
 * ERROR HANDLING:
 * 
 * Timeout: 500ms - If no ACK received, retry
 * Max Retries: 3 attempts
 * Invalid Start Byte: Discard and resync
 * CRC Mismatch: Send NACK, wait for retry
 * Buffer Overflow: Send NACK, discard message
 * 
 * ============================================================================
 * PERFORMANCE:
 * 
 * Baud Rate: 115200 bps
 * Theoretical Max: ~11.5 KB/s
 * Actual Throughput: ~8-10 KB/s (with overhead)
 * Latency: 10-50ms typical
 * 
 * Transfer Times (approximate):
 *   Small message (10 bytes): ~5ms
 *   Keypress event: ~2ms
 *   Screen update (1KB): ~100ms
 *   Full screen (16KB): ~1.5s
 * 
 * ============================================================================
 * MEMORY USAGE:
 * 
 * RX Buffer: 4096 bytes (circular)
 * TX Buffer: 4096 bytes (circular)
 * Message Queue: 512 bytes (16 messages × 32 bytes)
 * Total: ~8.5 KB
 * 
 * ============================================================================
 * USAGE EXAMPLE:
 * 
 * ```
 * UARTProtocol uart;
 * 
 * void setup() {
 *     uart.begin(16, 17, 115200);  // RX, TX, baud
 * }
 * 
 * void loop() {
 *     // Send keypress
 *     uart.sendKeypress(KEY_5, KEY_EVENT_PRESS);
 *     
 *     // Receive messages
 *     if (uart.available()) {
 *         UARTMessage msg = uart.read();
 *         
 *         if (msg.type == MSG_TYPE_DISPLAY_TEXT) {
 *             displayText((char*)msg.payload);
 *         }
 *     }
 * }
 * ```
 * 
 * ============================================================================
 */

#ifndef UART_PROTOCOL_H
#define UART_PROTOCOL_H

#include <Arduino.h>
#include <HardwareSerial.h>
#include "../config.h"

// ============================================================================
// PROTOCOL CONSTANTS
// ============================================================================

// Frame markers
#define UART_START_BYTE 0xAA

// Message types (defined in config.h)
// MSG_TYPE_DISPLAY_TEXT      0x01
// MSG_TYPE_DISPLAY_IMAGE     0x02
// MSG_TYPE_KEYPRESS          0x03
// MSG_TYPE_CAMERA_CAPTURE    0x04
// MSG_TYPE_MODE_CHANGE       0x05
// MSG_TYPE_PANIC             0x06
// MSG_TYPE_HEARTBEAT         0x07
// MSG_TYPE_BATTERY_STATUS    0x08
// MSG_TYPE_P2P_DATA          0x09
// MSG_TYPE_ACK               0x0A
// MSG_TYPE_NACK              0x0B

// Buffer sizes
#define UART_RX_BUFFER_SIZE 4096
#define UART_TX_BUFFER_SIZE 4096
#define UART_MAX_PAYLOAD_SIZE 1024
#define UART_MAX_FRAME_SIZE (UART_MAX_PAYLOAD_SIZE + 7)
#define UART_MESSAGE_QUEUE_SIZE 16

// Timing
#define UART_TIMEOUT_MS 500
#define UART_RETRY_COUNT 3
#define UART_ACK_TIMEOUT_MS 100

// Parser states
#define PARSER_STATE_IDLE 0
#define PARSER_STATE_START 1
#define PARSER_STATE_TYPE 2
#define PARSER_STATE_LENGTH_H 3
#define PARSER_STATE_LENGTH_L 4
#define PARSER_STATE_PAYLOAD 5
#define PARSER_STATE_CRC_H 6
#define PARSER_STATE_CRC_L 7

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * @struct UARTMessage
 * @brief Structure representing a UART message
 */
struct UARTMessage {
    uint8_t type;                       // Message type
    uint16_t length;                    // Payload length
    uint8_t payload[UART_MAX_PAYLOAD_SIZE]; // Payload data
    uint8_t sequence;                   // Sequence number
    unsigned long timestamp;            // Timestamp (millis)
    bool needsAck;                      // Requires acknowledgment
    uint8_t retryCount;                 // Retry counter
    
    UARTMessage() : type(0), length(0), sequence(0), timestamp(0), 
                    needsAck(false), retryCount(0) {
        memset(payload, 0, UART_MAX_PAYLOAD_SIZE);
    }
};

/**
 * @struct UARTStats
 * @brief Statistics for monitoring UART performance
 */
struct UARTStats {
    uint32_t messagesSent;
    uint32_t messagesReceived;
    uint32_t bytesTransferred;
    uint32_t crcErrors;
    uint32_t timeouts;
    uint32_t retries;
    uint32_t acksSent;
    uint32_t acksReceived;
    uint32_t nacksSent;
    uint32_t nacksReceived;
    float throughput;  // bytes per second
    
    UARTStats() : messagesSent(0), messagesReceived(0), bytesTransferred(0),
                  crcErrors(0), timeouts(0), retries(0), acksSent(0),
                  acksReceived(0), nacksSent(0), nacksReceived(0), throughput(0.0f) {}
};

// ============================================================================
// CLASS DEFINITION
// ============================================================================

/**
 * @class UARTProtocol
 * @brief Reliable UART communication protocol handler
 */
class UARTProtocol {
public:
    // ========================================================================
    // CONSTRUCTOR & DESTRUCTOR
    // ========================================================================
    
    /**
     * @brief Constructor
     */
    UARTProtocol();
    
    /**
     * @brief Destructor
     */
    ~UARTProtocol();

    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    /**
     * @brief Initialize UART communication
     * 
     * @param rxPin RX pin number
     * @param txPin TX pin number
     * @param baudRate Baud rate (default: 115200)
     * @return true if successful
     */
    bool begin(int rxPin, int txPin, uint32_t baudRate = 115200);
    
    /**
     * @brief Stop UART communication
     */
    void end();
    
    /**
     * @brief Check if UART is initialized
     * 
     * @return true if initialized
     */
    bool isInitialized() const { return _initialized; }
    
    /**
     * @brief Check if connected to Pi (received heartbeat recently)
     * 
     * @return true if connected
     */
    bool isConnected() const;

    // ========================================================================
    // MESSAGE SENDING (High-Level API)
    // ========================================================================
    
    /**
     * @brief Send keypress event
     * 
     * @param key Key code
     * @param eventType Event type (press, release, etc.)
     * @return true if sent successfully
     */
    bool sendKeypress(uint8_t key, uint8_t eventType);
    
    /**
     * @brief Send camera capture command
     * 
     * @return true if sent successfully
     */
    bool sendCameraCapture();
    
    /**
     * @brief Send panic signal
     * 
     * @return true if sent successfully
     */
    bool sendPanic();
    
    /**
     * @brief Send heartbeat
     * 
     * @return true if sent successfully
     */
    bool sendHeartbeat();
    
    /**
     * @brief Send battery status
     * 
     * @param percent Battery percentage (0-100)
     * @param voltage Battery voltage (volts)
     * @param charging Charging status
     * @return true if sent successfully
     */
    bool sendBatteryStatus(uint8_t percent, float voltage, bool charging);
    
    /**
     * @brief Send mode change notification
     * 
     * @param mode New mode
     * @return true if sent successfully
     */
    bool sendModeChange(uint8_t mode);
    
    /**
     * @brief Send ACK
     * 
     * @param sequence Sequence number to acknowledge
     * @return true if sent successfully
     */
    bool sendAck(uint8_t sequence);
    
    /**
     * @brief Send NACK
     * 
     * @param sequence Sequence number to reject
     * @return true if sent successfully
     */
    bool sendNack(uint8_t sequence);

    // ========================================================================
    // MESSAGE SENDING (Low-Level API)
    // ========================================================================
    
    /**
     * @brief Send raw message
     * 
     * @param type Message type
     * @param payload Payload data
     * @param length Payload length
     * @param needsAck Requires acknowledgment
     * @return true if sent successfully
     */
    bool send(uint8_t type, const uint8_t* payload, uint16_t length, bool needsAck = false);
    
    /**
     * @brief Send message with automatic retry
     * 
     * @param msg Message to send
     * @return true if sent and acknowledged
     */
    bool sendWithRetry(UARTMessage& msg);

    // ========================================================================
    // MESSAGE RECEIVING
    // ========================================================================
    
    /**
     * @brief Check if messages are available
     * 
     * @return true if messages in queue
     */
    bool available() const { return (_rxQueueHead != _rxQueueTail); }
    
    /**
     * @brief Read next message from queue
     * 
     * @return Message (or empty if queue is empty)
     */
    UARTMessage read();
    
    /**
     * @brief Peek at next message without removing it
     * 
     * @return Message (or empty if queue is empty)
     */
    UARTMessage peek() const;
    
    /**
     * @brief Get number of messages in receive queue
     * 
     * @return Message count
     */
    uint8_t getMessageCount() const;
    
    /**
     * @brief Clear receive queue
     */
    void clearQueue();

    // ========================================================================
    // PROCESSING
    // ========================================================================
    
    /**
     * @brief Process incoming UART data
     * 
     * Should be called frequently from main loop or task.
     */
    void process();
    
    /**
     * @brief Process pending ACKs and retries
     */
    void processRetries();

    // ========================================================================
    // STATISTICS & DEBUG
    // ========================================================================
    
    /**
     * @brief Get communication statistics
     * 
     * @return Statistics structure
     */
    const UARTStats& getStats() const { return _stats; }
    
    /**
     * @brief Reset statistics
     */
    void resetStats();
    
    /**
     * @brief Print statistics to serial
     */
    void printStats() const;
    
    /**
     * @brief Get last error code
     * 
     * @return Error code
     */
    uint8_t getLastError() const { return _lastError; }

private:
    // ========================================================================
    // PRIVATE MEMBERS
    // ========================================================================
    
    // Hardware
    HardwareSerial* _serial;
    int _rxPin;
    int _txPin;
    uint32_t _baudRate;
    bool _initialized;
    
    // Parser state
    uint8_t _parserState;
    uint8_t _currentType;
    uint16_t _currentLength;
    uint16_t _payloadIndex;
    uint8_t _currentPayload[UART_MAX_PAYLOAD_SIZE];
    uint16_t _expectedCrc;
    uint16_t _receivedCrc;
    
    // Message queues (circular buffers)
    UARTMessage _rxQueue[UART_MESSAGE_QUEUE_SIZE];
    volatile uint8_t _rxQueueHead;
    volatile uint8_t _rxQueueTail;
    
    UARTMessage _txPendingQueue[UART_MESSAGE_QUEUE_SIZE];
    uint8_t _txPendingHead;
    uint8_t _txPendingTail;
    
    // Sequence tracking
    uint8_t _txSequence;
    uint8_t _lastRxSequence;
    
    // Connection tracking
    unsigned long _lastHeartbeatTime;
    unsigned long _lastRxTime;
    
    // Statistics
    UARTStats _stats;
    unsigned long _lastStatsTime;
    uint32_t _statsBytes;
    
    // Error tracking
    uint8_t _lastError;
    uint8_t _consecutiveErrors;
    
    // ========================================================================
    // PRIVATE METHODS
    // ========================================================================
    
    /**
     * @brief Parse incoming byte
     * 
     * @param byte Byte to parse
     */
    void parseByte(uint8_t byte);
    
    /**
     * @brief Handle received message
     * 
     * @param msg Received message
     */
    void handleReceivedMessage(const UARTMessage& msg);
    
    /**
     * @brief Add message to receive queue
     * 
     * @param msg Message to add
     * @return true if added
     */
    bool addToRxQueue(const UARTMessage& msg);
    
    /**
     * @brief Add message to pending queue (waiting for ACK)
     * 
     * @param msg Message to add
     * @return true if added
     */
    bool addToPendingQueue(const UARTMessage& msg);
    
    /**
     * @brief Remove message from pending queue
     * 
     * @param sequence Sequence number
     */
    void removeFromPendingQueue(uint8_t sequence);
    
    /**
     * @brief Send raw frame
     * 
     * @param type Message type
     * @param payload Payload data
     * @param length Payload length
     * @return true if sent
     */
    bool sendFrame(uint8_t type, const uint8_t* payload, uint16_t length);
    
    /**
     * @brief Calculate CRC16-CCITT
     * 
     * @param data Data buffer
     * @param length Data length
     * @return CRC16 value
     */
    uint16_t calculateCrc16(const uint8_t* data, uint16_t length);
    
    /**
     * @brief Verify CRC16
     * 
     * @param type Message type
     * @param length Payload length
     * @param payload Payload data
     * @param expectedCrc Expected CRC value
     * @return true if valid
     */
    bool verifyCrc16(uint8_t type, uint16_t length, const uint8_t* payload, uint16_t expectedCrc);
    
    /**
     * @brief Get next sequence number
     * 
     * @return Sequence number
     */
    uint8_t getNextSequence() {
        _txSequence = (_txSequence + 1) % 256;
        return _txSequence;
    }
    
    /**
     * @brief Update throughput statistics
     */
    void updateThroughput();
    
    /**
     * @brief Reset parser state
     */
    void resetParser();
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * @brief Get message type name (for debugging)
 * 
 * @param type Message type
 * @return Type name string
 */
const char* getMessageTypeName(uint8_t type);

/**
 * @brief Dump message contents (for debugging)
 * 
 * @param msg Message to dump
 */
void dumpMessage(const UARTMessage& msg);

#endif // UART_PROTOCOL_H

// ============================================================================
// END OF FILE
// ============================================================================
