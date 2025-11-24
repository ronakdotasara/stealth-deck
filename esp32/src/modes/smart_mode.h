/**
 * ============================================================================
 * smart_mode.h - Smart/AI Mode for Stealth Deck
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-24
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Smart mode implementation for AI-powered features.
 * Handles query input, response display, and AI interaction.
 * 
 * Features:
 * - Text query input using T9
 * - Gemini AI integration via Pi
 * - Response display
 * - History management
 * - Image capture & analysis
 * - Web search
 * 
 * ============================================================================
 */

#ifndef SMART_MODE_H
#define SMART_MODE_H

#include <Arduino.h>

#define MAX_QUERY_LENGTH 256
#define MAX_RESPONSE_LENGTH 2048
#define MAX_HISTORY_ENTRIES 10

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
    char query[MAX_QUERY_LENGTH];
    char response[MAX_RESPONSE_LENGTH];
    QueryType type;
    unsigned long timestamp;
};

class SmartMode {
public:
    SmartMode();
    
    void begin();
    void reset();
    void update();
    
    void handleKey(uint8_t key);
    void handleTextInput(char c);
    void handleBackspace();
    void handleSubmit();
    void handleCancel();
    
    void handleCameraCapture();
    void handleWebSearch();
    void handleVoiceInput();
    
    void displayResponse(const char* response);
    void displayError(const char* error);
    void displayWaiting();
    
    void scrollUp();
    void scrollDown();
    
    const char* getCurrentQuery();
    const char* getCurrentResponse();
    SmartModeState getState();
    
    void addToHistory(const char* query, const char* response, QueryType type);
    QueryHistory* getHistory(uint8_t index);
    uint8_t getHistoryCount();
    void clearHistory();
    
    bool isWaitingForResponse();
    void setResponseReceived(bool received);
    
private:
    char queryBuffer[MAX_QUERY_LENGTH];
    char responseBuffer[MAX_RESPONSE_LENGTH];
    
    uint16_t queryCursor;
    uint16_t responseScrollOffset;
    
    SmartModeState state;
    QueryType currentQueryType;
    
    QueryHistory history[MAX_HISTORY_ENTRIES];
    uint8_t historyCount;
    uint8_t historyIndex;
    
    unsigned long lastInputTime;
    unsigned long waitStartTime;
    
    bool responseReceived;
    
    void updateDisplay();
    void displayQueryInput();
    void displayResponseText();
    
    void sendQueryToPI();
    void requestCameraCapture();
    void requestWebSearch();
    
    void clearQuery();
    void clearResponse();
};

#endif
