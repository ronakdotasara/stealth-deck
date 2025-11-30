/**
 * ============================================================================
 * smart_mode.cpp - Smart/AI Mode Implementation
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-30
 * Author: Stealth Deck Project
 * License: MIT
 * ============================================================================
 */

#include "smart_mode.h"
#include "../communication/uart_protocol.h"
#include "../display/display_driver.h"

extern UARTProtocol uart;
extern DisplayDriver display;

// ============================================================================
// CONSTRUCTOR
// ============================================================================

SmartMode::SmartMode() :
    queryCursor(0),
    responseScrollOffset(0),
    state(SMART_STATE_IDLE),
    currentQueryType(QUERY_TYPE_TEXT),
    historyCount(0),
    historyIndex(0),
    lastInputTime(0),
    waitStartTime(0),
    responseReceived(false)
{
    memset(queryBuffer, 0, sizeof(queryBuffer));
    memset(responseBuffer, 0, sizeof(responseBuffer));
    memset(history, 0, sizeof(history));
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void SmartMode::begin() {
    Serial.println("│ ✓ Smart mode ready");
    reset();
}

void SmartMode::reset() {
    queryCursor = 0;
    responseScrollOffset = 0;
    state = SMART_STATE_IDLE;
    currentQueryType = QUERY_TYPE_TEXT;
    responseReceived = false;
    
    clearQuery();
    clearResponse();
    
    Serial.println("Smart mode reset");
}

void SmartMode::update() {
    unsigned long now = millis();
    
    switch (state) {
        case SMART_STATE_IDLE:
            // Display idle screen
            break;
            
        case SMART_STATE_ENTERING_QUERY:
            // Update query input display
            updateDisplay();
            break;
            
        case SMART_STATE_WAITING_RESPONSE:
            // Show waiting animation
            if (now - waitStartTime > 30000) {
                // Timeout after 30 seconds
                displayError("Response timeout");
                state = SMART_STATE_ERROR;
            }
            break;
            
        case SMART_STATE_DISPLAYING_RESPONSE:
            // Display response
            updateDisplay();
            break;
            
        case SMART_STATE_ERROR:
            // Display error state
            break;
    }
}

// ============================================================================
// KEY HANDLING
// ============================================================================

void SmartMode::handleKey(uint8_t key) {
    Serial.printf("Smart mode key: 0x%02X (state: %d)\n", key, state);
    
    switch (state) {
        case SMART_STATE_IDLE:
        case SMART_STATE_ENTERING_QUERY:
            // Handle query input
            if (key >= KEY_0 && key <= KEY_9) {
                // Number keys - add to query
                handleTextInput('0' + (key - KEY_0));
            } else if (key == KEY_BACK) {
                handleBackspace();
            } else if (key == KEY_OK) {
                handleSubmit();
            } else if (key == KEY_FN) {
                handleCancel();
            }
            break;
            
        case SMART_STATE_DISPLAYING_RESPONSE:
            // Handle response navigation
            if (key == KEY_UP) {
                scrollUp();
            } else if (key == KEY_DOWN) {
                scrollDown();
            } else if (key == KEY_BACK) {
                // Return to query input
                state = SMART_STATE_ENTERING_QUERY;
                updateDisplay();
            }
            break;
            
        default:
            break;
    }
    
    lastInputTime = millis();
}

void SmartMode::handleTextInput(char c) {
    if (queryCursor < MAX_QUERY_LENGTH - 1) {
        queryBuffer[queryCursor++] = c;
        queryBuffer[queryCursor] = '\0';
        
        state = SMART_STATE_ENTERING_QUERY;
        updateDisplay();
        
        Serial.printf("Query: %s\n", queryBuffer);
    }
}

void SmartMode::handleBackspace() {
    if (queryCursor > 0) {
        queryCursor--;
        queryBuffer[queryCursor] = '\0';
        updateDisplay();
    }
}

void SmartMode::handleSubmit() {
    if (queryCursor > 0) {
        Serial.printf("Submitting query: %s\n", queryBuffer);
        
        state = SMART_STATE_WAITING_RESPONSE;
        waitStartTime = millis();
        
        sendQueryToPI();
        displayWaiting();
    }
}

void SmartMode::handleCancel() {
    reset();
    updateDisplay();
}

// ============================================================================
// SPECIAL FUNCTIONS
// ============================================================================

void SmartMode::handleCameraCapture() {
    Serial.println("Requesting camera capture...");
    currentQueryType = QUERY_TYPE_CAMERA;
    requestCameraCapture();
}

void SmartMode::handleWebSearch() {
    Serial.println("Requesting web search...");
    currentQueryType = QUERY_TYPE_SEARCH;
    requestWebSearch();
}

void SmartMode::handleVoiceInput() {
    Serial.println("Voice input not yet implemented");
    displayError("Voice input unavailable");
}

// ============================================================================
// DISPLAY FUNCTIONS
// ============================================================================

void SmartMode::updateDisplay() {
    display.clear();
    
    switch (state) {
        case SMART_STATE_IDLE:
        case SMART_STATE_ENTERING_QUERY:
            displayQueryInput();
            break;
            
        case SMART_STATE_WAITING_RESPONSE:
            displayWaiting();
            break;
            
        case SMART_STATE_DISPLAYING_RESPONSE:
            displayResponseText();
            break;
            
        case SMART_STATE_ERROR:
            // Error already displayed
            break;
    }
    
    display.flush();
}

void SmartMode::displayQueryInput() {
    // Title
    display.drawText(10, 10, "Smart Mode", COLOR_WHITE, 2);
    
    // Query prompt
    display.drawText(10, 40, "Enter query:", COLOR_WHITE, 1);
    
    // Query text
    display.drawRect(10, 60, 220, 100, COLOR_WHITE);
    display.drawText(15, 65, queryBuffer, COLOR_WHITE, 1);
    
    // Cursor
    if (millis() % 1000 < 500) {
        uint16_t cursorX = 15 + (queryCursor * 6);
        display.drawLine(cursorX, 75, cursorX, 85, COLOR_WHITE);
    }
    
    // Instructions
    display.drawText(10, 170, "OK: Submit", COLOR_WHITE, 1);
    display.drawText(10, 185, "BACK: Delete", COLOR_WHITE, 1);
    display.drawText(10, 200, "FN: Cancel", COLOR_WHITE, 1);
}

void SmartMode::displayResponse(const char* response) {
    if (!response) return;
    
    strncpy(responseBuffer, response, MAX_RESPONSE_LENGTH - 1);
    responseBuffer[MAX_RESPONSE_LENGTH - 1] = '\0';
    
    state = SMART_STATE_DISPLAYING_RESPONSE;
    responseScrollOffset = 0;
    responseReceived = true;
    
    // Add to history
    addToHistory(queryBuffer, responseBuffer, currentQueryType);
    
    updateDisplay();
}

void SmartMode::displayResponseText() {
    // Title
    display.drawText(10, 10, "Response:", COLOR_WHITE, 2);
    
    // Response area
    display.drawRect(10, 40, 220, 400, COLOR_WHITE);
    
    // Display response text with scrolling
    uint16_t y = 45 - responseScrollOffset;
    const char* text = responseBuffer;
    char line[40];
    uint8_t lineIndex = 0;
    
    while (*text && y < 440) {
        if (*text == '\n' || lineIndex >= 39) {
            line[lineIndex] = '\0';
            if (y >= 40 && y < 440) {
                display.drawText(15, y, line, COLOR_WHITE, 1);
            }
            y += 15;
            lineIndex = 0;
            if (*text == '\n') text++;
        } else {
            line[lineIndex++] = *text++;
        }
    }
    
    // Print remaining text
    if (lineIndex > 0) {
        line[lineIndex] = '\0';
        if (y >= 40 && y < 440) {
            display.drawText(15, y, line, COLOR_WHITE, 1);
        }
    }
    
    // Instructions
    display.drawText(10, 450, "UP/DOWN: Scroll", COLOR_WHITE, 1);
    display.drawText(10, 465, "BACK: New Query", COLOR_WHITE, 1);
}

void SmartMode::displayError(const char* error) {
    display.clear();
    display.drawText(10, 250, "ERROR", COLOR_RED, 3);
    display.drawText(10, 290, error, COLOR_WHITE, 1);
    display.flush();
    
    state = SMART_STATE_ERROR;
}

void SmartMode::displayWaiting() {
    display.clear();
    display.drawText(60, 250, "Waiting...", COLOR_WHITE, 2);
    
    // Animated dots
    uint8_t dots = (millis() / 500) % 4;
    char dotStr[5] = "";
    for (uint8_t i = 0; i < dots; i++) {
        dotStr[i] = '.';
    }
    dotStr[dots] = '\0';
    display.drawText(100, 290, dotStr, COLOR_WHITE, 2);
    
    display.flush();
}

// ============================================================================
// SCROLLING
// ============================================================================

void SmartMode::scrollUp() {
    if (responseScrollOffset > 0) {
        responseScrollOffset -= 15;
        updateDisplay();
    }
}

void SmartMode::scrollDown() {
    responseScrollOffset += 15;
    updateDisplay();
}

// ============================================================================
// GETTERS
// ============================================================================

const char* SmartMode::getCurrentQuery() {
    return queryBuffer;
}

const char* SmartMode::getCurrentResponse() {
    return responseBuffer;
}

SmartModeState SmartMode::getState() {
    return state;
}

bool SmartMode::isWaitingForResponse() {
    return (state == SMART_STATE_WAITING_RESPONSE && !responseReceived);
}

void SmartMode::setResponseReceived(bool received) {
    responseReceived = received;
}

// ============================================================================
// HISTORY
// ============================================================================

void SmartMode::addToHistory(const char* query, const char* response, QueryType type) {
    if (historyCount < MAX_HISTORY_ENTRIES) {
        historyIndex = historyCount;
        historyCount++;
    } else {
        // Shift history
        for (uint8_t i = 0; i < MAX_HISTORY_ENTRIES - 1; i++) {
            history[i] = history[i + 1];
        }
        historyIndex = MAX_HISTORY_ENTRIES - 1;
    }
    
    strncpy(history[historyIndex].query, query, MAX_QUERY_LENGTH - 1);
    strncpy(history[historyIndex].response, response, MAX_RESPONSE_LENGTH - 1);
    history[historyIndex].type = type;
    history[historyIndex].timestamp = millis();
    
    Serial.printf("Added to history: %s\n", query);
}

QueryHistory* SmartMode::getHistory(uint8_t index) {
    if (index < historyCount) {
        return &history[index];
    }
    return nullptr;
}

uint8_t SmartMode::getHistoryCount() {
    return historyCount;
}

void SmartMode::clearHistory() {
    memset(history, 0, sizeof(history));
    historyCount = 0;
    historyIndex = 0;
    Serial.println("History cleared");
}

// ============================================================================
// COMMUNICATION WITH PI - FIXED VERSION
// ============================================================================

void SmartMode::sendQueryToPI() {
    Serial.println("═══════════════════════════════════════");
    Serial.println("Sending query to Pi via UART...");
    Serial.printf("Query: %s\n", queryBuffer);
    Serial.println("═══════════════════════════════════════");
    
    // TODO: Implement proper UART protocol when ready
    // For now, just log to serial and simulate response
    
    // Simulate AI response after 2 seconds
    delay(2000);
    
    // Create simulated response
    char response[MAX_RESPONSE_LENGTH];
    snprintf(response, MAX_RESPONSE_LENGTH,
             "DEMO MODE - Pi not connected\n\n"
             "Your query:\n%s\n\n"
             "This is a simulated response.\n"
             "Connect Raspberry Pi for real\n"
             "AI-powered answers.",
             queryBuffer);
    
    displayResponse(response);
    Serial.println("Simulated response displayed");
}

void SmartMode::requestCameraCapture() {
    Serial.println("═══════════════════════════════════════");
    Serial.println("Camera capture requested");
    Serial.println("═══════════════════════════════════════");
    
    // TODO: Send camera command via UART when protocol is ready
    displayError("Camera requires Pi");
}

void SmartMode::requestWebSearch() {
    Serial.println("═══════════════════════════════════════");
    Serial.println("Web search requested");
    Serial.printf("Query: %s\n", queryBuffer);
    Serial.println("═══════════════════════════════════════");
    
    // TODO: Send search query via UART when protocol is ready
    displayError("Search requires Pi");
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

void SmartMode::clearQuery() {
    memset(queryBuffer, 0, sizeof(queryBuffer));
    queryCursor = 0;
}

void SmartMode::clearResponse() {
    memset(responseBuffer, 0, sizeof(responseBuffer));
    responseScrollOffset = 0;
}

// ============================================================================
// END OF FILE
// ============================================================================
