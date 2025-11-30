/**
 * ============================================================================
 * smart_mode.h - Smart/AI Mode for Stealth Deck
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-30
 * Author: Stealth Deck Project
 * License: MIT
 * ============================================================================
 */

#ifndef SMART_MODE_H
#define SMART_MODE_H

#include <Arduino.h>
#include "../config.h"      // ✅ MAX_QUERY_LENGTH, MAX_RESPONSE_LENGTH, MAX_HISTORY_ENTRIES
#include "../input/keypad.h" // ✅ KeyEvent type

// ============================================================================
// SMART MODE CONSTANTS (Use config.h values)
// ============================================================================

// MAX_QUERY_LENGTH     = 128  (from config.h)
// MAX_RESPONSE_LENGTH  = 512  (from config.h) 
// MAX_HISTORY_ENTRIES  = 10   (from config.h)

enum SmartModeState {
    SMART_STATE_IDLE,
    SMART_STATE_ENTERING_QUERY,
    SMART_STATE_WAITING_RESPONSE,
    SMART_STATE_DISPLAYING_RESPONSE,
    SMART_STATE_ERROR
};

enum QueryType {
    QUERY_TYPE_TEXT,
    QUERY_TYPE_CAMERA,
    QUERY_TYPE_SEARCH,
    QUERY_TYPE_VOICE
};

struct QueryHistory {
    char query[MAX_QUERY_LENGTH];      // ✅ Uses config.h constant
    char response[MAX_RESPONSE_LENGTH]; // ✅ Uses config.h constant
    QueryType type;
    unsigned long timestamp;
};

class SmartMode {
public:
    SmartMode();
    
    void begin();
    void reset();
    void update();
    
    // Main integration methods
    void activate() {
        Serial.println("Smart mode activated");
        reset();
    }
    
    void deactivate() {
        Serial.println("Smart mode deactivated");
    }
    
    void handleKeyEvent(KeyEvent event) {
        if (event.type == KEY_EVENT_PRESS) {
            handleKey(event.key);
        }
    }
    
    // Input handling
    void handleKey(uint8_t key);
    void handleTextInput(char c);
    void handleBackspace();
    void handleSubmit();
    void handleCancel();
    
    // Query types
    void handleCameraCapture();
    void handleWebSearch();
    void handleVoiceInput();
    
    // Display
    void displayResponse(const char* response);
    void displayError(const char* error);
    void displayWaiting();
    
    void scrollUp();
    void scrollDown();
    
    // Getters
    const char* getCurrentQuery();
    const char* getCurrentResponse();
    SmartModeState getState();
    
    // History
    void addToHistory(const char* query, const char* response, QueryType type);
    QueryHistory* getHistory(uint8_t index);
    uint8_t getHistoryCount();
    void clearHistory();
    
    // State
    bool isWaitingForResponse();
    void setResponseReceived(bool received);

private:
    char queryBuffer[MAX_QUERY_LENGTH];     // ✅ Fixed size
    char responseBuffer[MAX_RESPONSE_LENGTH]; // ✅ Fixed size
    
    uint16_t queryCursor;
    uint16_t responseScrollOffset;
    
    SmartModeState state;
    QueryType currentQueryType;
    
    QueryHistory history[MAX_HISTORY_ENTRIES]; // ✅ Fixed size
    uint8_t historyCount;
    uint8_t historyIndex;
    
    unsigned long lastInputTime;
    unsigned long waitStartTime;
    
    bool responseReceived;
    
    // Private methods
    void updateDisplay();
    void displayQueryInput();
    void displayResponseText();
    
    void sendQueryToPI();
    void requestCameraCapture();
    void requestWebSearch();
    
    void clearQuery();
    void clearResponse();
};

#endif // SMART_MODE_H
