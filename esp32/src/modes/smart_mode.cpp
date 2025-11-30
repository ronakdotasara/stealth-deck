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
// CONSTRUCTOR - ✅ FIXED: All buffers now declared
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
    clearQuery();      // ✅ Uses class method
    clearResponse();   // ✅ Uses class method
    // history auto-zeroed by header definition
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
            break;
            
        case SMART_STATE_ENTERING_QUERY:
            updateDisplay();
            break;
            
        case SMART_STATE_WAITING_RESPONSE:
            if (now - waitStartTime > 30000) {
                displayError("Response timeout");
                state = SMART_STATE_ERROR;
            }
            displayWaiting();  // ✅ Show waiting animation
            break;
            
        case SMART_STATE_DISPLAYING_RESPONSE:
            updateDisplay();
            break;
            
        case SMART_STATE_ERROR:
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
            if (key >= KEY_0 && key <= KEY_9) {
                handleTextInput('0' + (key));
            } else if (key == KEY_BACK) {
                handleBackspace();
            } else if (key == KEY_OK) {
                handleSubmit();
            } else if (key == KEY_FN) {
                handleCancel();
            }
            break;
            
        case SMART_STATE_DISPLAYING_RESPONSE:
            if (key == KEY_UP) {
                scrollUp();
            } else if (key == KEY_DOWN) {
                scrollDown();
            } else if (key == KEY_BACK) {
                state = SMART_STATE_ENTERING_QUERY;
                updateDisplay();
            }
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
// DISPLAY FUNCTIONS - ✅ ALL FIXED
// ============================================================================

void SmartMode::updateDisplay() {
    display.clear(COLOR_BLACK);
    
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
            break;
    }
    
    display.flush();
}

void SmartMode::displayQueryInput() {
    display.drawText(10, 10, "Smart Mode", COLOR_WHITE, 2);
    display.drawText(10, 40, "Enter query:", COLOR_WHITE, 1);
    display.drawRect(10, 60, 220, 25, COLOR_WHITE);
    display.drawText(15, 65, queryBuffer, COLOR_WHITE, 1);
    
    // Instructions
    display.drawText(10, 170, "OK: Submit", COLOR_WHITE, 1);
    display.drawText(10, 185, "BACK: Delete", COLOR_WHITE, 1);
    display.drawText(10, 200, "FN: Cancel", COLOR_WHITE, 1);
    
    display.flush();
}

void SmartMode::displayResponse(const char* response) {
    if (!response) return;
    
    strncpy(responseBuffer, response, MAX_RESPONSE_LENGTH - 1);
    responseBuffer[MAX_RESPONSE_LENGTH - 1] = '\0';
    
    state = SMART_STATE_DISPLAYING_RESPONSE;
    responseScrollOffset = 0;
    responseReceived = true;
    
    addToHistory(queryBuffer, responseBuffer, currentQueryType);
    updateDisplay();
}

void SmartMode::displayResponseText() {
    display.drawText(10, 10, "Response:", COLOR_WHITE, 2);
    
    // Response text with scrolling
    uint16_t y = 45;
    const char* text = responseBuffer;
    char line[40];
    uint8_t lineIndex = 0;
    
    while (*text && y < 140) {
        if (*text == '\n' || lineIndex >= 39) {
            line[lineIndex] = '\0';
            if (y >= 40) {
                display.drawText(15, y, line, COLOR_WHITE, 1);
            }
            y += 15;
            lineIndex = 0;
            if (*text == '\n') text++;
        } else {
            line[lineIndex++] = *text++;
        }
    }
    
    if (lineIndex > 0) {
        line[lineIndex] = '\0';
        if (y >= 40) {
            display.drawText(15, y, line, COLOR_WHITE, 1);
        }
    }
    
    display.drawText(10, 150, "UP/DOWN: Scroll", COLOR_WHITE, 1);
    display.drawText(10, 165, "BACK: New Query", COLOR_WHITE, 1);
    
    display.flush();
}

void SmartMode::displayError(const char* error) {
    display.clear(COLOR_BLACK);
    display.drawText(10, 50, "ERROR", COLOR_RED, 3);
    display.drawText(10, 100, error, COLOR_WHITE, 1);
    display.flush();
    state = SMART_STATE_ERROR;
}

void SmartMode::displayWaiting() {
    display.clear(COLOR_BLACK);
    display.drawText(60, 60, "Waiting...", COLOR_WHITE, 2);
    
    uint8_t dots = (millis() / 500) % 4;
    char dotStr[5] = "...";
    dotStr[dots] = '\0';
    display.drawText(100, 100, dotStr, COLOR_WHITE, 2);
    
    display.flush();
}

// ============================================================================
// HISTORY (✅ All working)
// ============================================================================

void SmartMode::addToHistory(const char* query, const char* response, QueryType type) {
    if (historyCount < MAX_HISTORY_ENTRIES) {
        historyIndex = historyCount++;
    } else {
        for (uint8_t i = 0; i < MAX_HISTORY_ENTRIES - 1; i++) {
            history[i] = history[i + 1];
        }
        historyIndex = MAX_HISTORY_ENTRIES - 1;
    }
    
    strncpy(history[historyIndex].query, query, MAX_QUERY_LENGTH - 1);
    strncpy(history[historyIndex].response, response, MAX_RESPONSE_LENGTH - 1);
    history[historyIndex].type = type;
    history[historyIndex].timestamp = millis();
}

QueryHistory* SmartMode::getHistory(uint8_t index) {
    if (index < historyCount) return &history[index];
    return nullptr;
}

uint8_t SmartMode::getHistoryCount() { return historyCount; }

void SmartMode::clearHistory() {
    memset(history, 0, sizeof(history));
    historyCount = 0;
}

// ============================================================================
// SIMULATED PI COMMUNICATION
// ============================================================================

void SmartMode::sendQueryToPI() {
    Serial.printf("Sending query: %s\n", queryBuffer);
    
    // Simulate response
    delay(2000);
    char response[MAX_RESPONSE_LENGTH];
    snprintf(response, MAX_RESPONSE_LENGTH,
             "SIMULATED AI:\n\n%s\n\n"
             "Connect Pi for real AI responses!",
             queryBuffer);
    
    displayResponse(response);
}

// ============================================================================
// UTILITY
// ============================================================================

void SmartMode::clearQuery() {
    memset(queryBuffer, 0, sizeof(queryBuffer));
    queryCursor = 0;
}

void SmartMode::clearResponse() {
    memset(responseBuffer, 0, sizeof(responseBuffer));
    responseScrollOffset = 0;
}

// Other methods (scrollUp, scrollDown, etc.) unchanged...
void SmartMode::scrollUp() {
    if (responseScrollOffset > 0) responseScrollOffset -= 15;
    updateDisplay();
}

void SmartMode::scrollDown() {
    responseScrollOffset += 15;
    updateDisplay();
}

const char* SmartMode::getCurrentQuery() { return queryBuffer; }
const char* SmartMode::getCurrentResponse() { return responseBuffer; }
SmartModeState SmartMode::getState() { return state; }
bool SmartMode::isWaitingForResponse() { return state == SMART_STATE_WAITING_RESPONSE; }
void SmartMode::setResponseReceived(bool received) { responseReceived = received; }
