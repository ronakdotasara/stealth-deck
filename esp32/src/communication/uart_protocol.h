/**
 * ============================================================================
 * @file uart_protocol.h
 * @brief UART Communication Protocol for ESP32 ↔ Raspberry Pi
 * @version 1.0.0
 * @date 2025-11-30
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * [Keep all your header comments the same]
 * ============================================================================
 */


#ifndef UART_PROTOCOL_H
#define UART_PROTOCOL_H


#include <Arduino.h>
#include <HardwareSerial.h>
#include "config.h"  // CHANGED from "../config.h"


// ============================================================================
// PROTOCOL CONSTANTS
// ============================================================================


// Frame markers
#define UART_START_BYTE 0xAA


// Message types are defined in config.h
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


// Buffer sizes - REMOVED DUPLICATES, using values from config.h
// UART_RX_BUFFER_SIZE is in config.h (2048)
// UART_TX_BUFFER_SIZE is in config.h (2048)
// UART_TIMEOUT_MS is in config.h (1000)

#define UART_MAX_PAYLOAD_SIZE 1024
#define UART_MAX_FRAME_SIZE (UART_MAX_PAYLOAD_SIZE + 7)
#define UART_MESSAGE_QUEUE_SIZE 16


// Timing - using UART_TIMEOUT_MS from config.h
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
    
    UARTProtocol();
    ~UARTProtocol();


    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    bool begin(int rxPin, int txPin, uint32_t baudRate = 115200);
    void end();
    bool isInitialized() const { return _initialized; }
    bool isConnected() const;


    // ========================================================================
    // MESSAGE SENDING (High-Level API)
    // ========================================================================
    
    bool sendKeypress(uint8_t key, uint8_t eventType);
    bool sendCameraCapture();
    bool sendPanic();
    bool sendHeartbeat();
    bool sendBatteryStatus(uint8_t percent, float voltage, bool charging);
    bool sendModeChange(uint8_t mode);
    bool sendAck(uint8_t sequence);
    bool sendNack(uint8_t sequence);


    // ========================================================================
    // MESSAGE SENDING (Low-Level API)
    // ========================================================================
    
    bool send(uint8_t type, const uint8_t* payload, uint16_t length, bool needsAck = false);
    bool sendWithRetry(UARTMessage& msg);


    // ========================================================================
    // MESSAGE RECEIVING
    // ========================================================================
    
    bool available() const { return (_rxQueueHead != _rxQueueTail); }
    UARTMessage read();
    UARTMessage peek() const;
    uint8_t getMessageCount() const;
    void clearQueue();


    // ========================================================================
    // PROCESSING
    // ========================================================================
    
    void process();
    void processRetries();


    // ========================================================================
    // STATISTICS & DEBUG
    // ========================================================================
    
    const UARTStats& getStats() const { return _stats; }
    void resetStats();
    void printStats() const;
    uint8_t getLastError() const { return _lastError; }


private:
    // ========================================================================
    // PRIVATE MEMBERS
    // ========================================================================
    
    HardwareSerial* _serial;
    int _rxPin;
    int _txPin;
    uint32_t _baudRate;
    bool _initialized;
    
    uint8_t _parserState;
    uint8_t _currentType;
    uint16_t _currentLength;
    uint16_t _payloadIndex;
    uint8_t _currentPayload[UART_MAX_PAYLOAD_SIZE];
    uint16_t _expectedCrc;
    uint16_t _receivedCrc;
    
    UARTMessage _rxQueue[UART_MESSAGE_QUEUE_SIZE];
    volatile uint8_t _rxQueueHead;
    volatile uint8_t _rxQueueTail;
    
    UARTMessage _txPendingQueue[UART_MESSAGE_QUEUE_SIZE];
    uint8_t _txPendingHead;
    uint8_t _txPendingTail;
    
    uint8_t _txSequence;
    uint8_t _lastRxSequence;
    
    unsigned long _lastHeartbeatTime;
    unsigned long _lastRxTime;
    
    UARTStats _stats;
    unsigned long _lastStatsTime;
    uint32_t _statsBytes;
    
    uint8_t _lastError;
    uint8_t _consecutiveErrors;
    
    // ========================================================================
    // PRIVATE METHODS
    // ========================================================================
    
    void parseByte(uint8_t byte);
    void handleReceivedMessage(const UARTMessage& msg);
    bool addToRxQueue(const UARTMessage& msg);
    bool addToPendingQueue(const UARTMessage& msg);
    void removeFromPendingQueue(uint8_t sequence);
    bool sendFrame(uint8_t type, const uint8_t* payload, uint16_t length);
    uint16_t calculateCrc16(const uint8_t* data, uint16_t length);
    bool verifyCrc16(uint8_t type, uint16_t length, const uint8_t* payload, uint16_t expectedCrc);
    
    uint8_t getNextSequence() {
        _txSequence = (_txSequence + 1) % 256;
        return _txSequence;
    }
    
    void updateThroughput();
    void resetParser();
};


// ============================================================================
// HELPER FUNCTIONS
// ============================================================================


const char* getMessageTypeName(uint8_t type);
void dumpMessage(const UARTMessage& msg);


#endif // UART_PROTOCOL_H
