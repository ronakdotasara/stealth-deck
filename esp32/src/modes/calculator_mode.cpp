/**
 * ============================================================================
 * calculator_mode.cpp - Calculator Mode Implementation
 * ============================================================================
 */

#include "calculator_mode.h"
#include "../display/display_driver.h"
#include <math.h>

extern DisplayDriver display;

// ============================================================================
// CONSTRUCTOR
// ============================================================================

CalculatorMode::CalculatorMode() {
    reset();
}

void CalculatorMode::begin() {
    reset();
    generateFakeHistory();
    updateDisplay();  // ✅ Show initial screen
}

void CalculatorMode::reset() {
    currentValue = 0.0;
    storedValue = 0.0;
    memoryValue = 0.0;
    
    currentOperator = OP_NONE;
    state = CALC_STATE_IDLE;
    
    hasDecimal = false;
    decimalPlaces = 0;
    
    memset(displayBuffer, 0, sizeof(displayBuffer));
    memset(expressionBuffer, 0, sizeof(expressionBuffer));
    
    strcpy(displayBuffer, "0");
}

// ============================================================================
// KEY HANDLING - ✅ FIXED FOR KEYPAD CODES
// ============================================================================

void CalculatorMode::handleKey(uint8_t key) {
    Serial.printf("Calc key: %d (state: %d)\n", key, state);
    
    // ✅ FIXED: Map keypad keys to calculator functions
    switch (key) {
        case KEY_0: case KEY_1: case KEY_2: case KEY_3: case KEY_4:
        case KEY_5: case KEY_6: case KEY_7: case KEY_8: case KEY_9:
            handleDigit(key);  // ✅ 0-9 keys
            break;
            
        case KEY_PLUS:
            handleOperator(OP_ADD);
            break;
        case KEY_MINUS:
            handleOperator(OP_SUBTRACT);
            break;
        case KEY_OK:  // = (Enter)
            handleEquals();
            break;
        case KEY_BACK:  // C (Clear)
            handleClear();
            break;
        case KEY_HASH:  // . (Decimal)
            handleDecimal();
            break;
            
        case KEY_FIX:  // M+ (Memory Add)
            handleMemoryAdd();
            break;
        case KEY_STAR:  // M- (Memory Subtract) 
            handleMemorySubtract();
            break;
            
        case KEY_UP:  // MR (Memory Recall)
            handleMemoryRecall();
            break;
        case KEY_DOWN:  // MC (Memory Clear)
            handleMemoryClear();
            break;
            
        case KEY_FN:  // Backspace
            handleBackspace();
            break;
            
        default:
            break;
    }
    
    updateDisplay();  // ✅ Update screen after every key
}

void CalculatorMode::handleDigit(uint8_t digit) {
    if (state == CALC_STATE_RESULT_DISPLAYED || state == CALC_STATE_ERROR) {
        reset();
        state = CALC_STATE_ENTERING_NUMBER;
    }
    
    if (state == CALC_STATE_IDLE) {
        state = CALC_STATE_ENTERING_NUMBER;
        strcpy(displayBuffer, "");
    }
    
    if (strlen(displayBuffer) < MAX_DISPLAY_LENGTH - 1) {
        if (hasDecimal) decimalPlaces++;
        
        char digitStr[2] = {'0' + digit, '\0'};
        strcat(displayBuffer, digitStr);
        
        currentValue = atof(displayBuffer);
    }
}

void CalculatorMode::handleOperator(CalculatorOperator op) {
    if (state == CALC_STATE_ENTERING_NUMBER) {
        if (currentOperator != OP_NONE) calculate();
        else storedValue = currentValue;
    }
    
    currentOperator = op;
    state = CALC_STATE_ENTERING_OPERATOR;
    hasDecimal = false;
    decimalPlaces = 0;
    
    // Update expression buffer
    char opStr[8];
    switch (op) {
        case OP_ADD: strcpy(opStr, " + "); break;
        case OP_SUBTRACT: strcpy(opStr, " - "); break;
        case OP_MULTIPLY: strcpy(opStr, " × "); break;
        case OP_DIVIDE: strcpy(opStr, " ÷ "); break;
        default: strcpy(opStr, ""); break;
    }
    
    if (strlen(expressionBuffer) + strlen(displayBuffer) + strlen(opStr) < MAX_EXPRESSION_LENGTH) {
        strcat(expressionBuffer, displayBuffer);
        strcat(expressionBuffer, opStr);
    }
}

void CalculatorMode::handleEquals() {
    if (currentOperator != OP_NONE) {
        calculate();
        
        char resultStr[32];
        formatNumber(currentValue, resultStr, sizeof(resultStr));
        
        strcat(expressionBuffer, " = ");
        strcat(expressionBuffer, resultStr);
        addToHistory(expressionBuffer, currentValue);
        
        strcpy(displayBuffer, resultStr);
        state = CALC_STATE_RESULT_DISPLAYED;
        currentOperator = OP_NONE;
        memset(expressionBuffer, 0, sizeof(expressionBuffer));
    }
}

void CalculatorMode::handleClear() {
    reset();
}

void CalculatorMode::handleBackspace() {
    if (state == CALC_STATE_ENTERING_NUMBER) {
        size_t len = strlen(displayBuffer);
        if (len > 0) {
            if (displayBuffer[len - 1] == '.') {
                hasDecimal = false;
            } else if (hasDecimal) {
                decimalPlaces--;
            }
            displayBuffer[len - 1] = '\0';
            
            if (strlen(displayBuffer) == 0) {
                strcpy(displayBuffer, "0");
                state = CALC_STATE_IDLE;
            }
            
            currentValue = atof(displayBuffer);
        }
    }
}

void CalculatorMode::handleDecimal() {
    if (!hasDecimal && state != CALC_STATE_RESULT_DISPLAYED) {
        if (state == CALC_STATE_IDLE) {
            strcpy(displayBuffer, "0");
            state = CALC_STATE_ENTERING_NUMBER;
        }
        if (strlen(displayBuffer) < MAX_DISPLAY_LENGTH - 1) {
            strcat(displayBuffer, ".");
            hasDecimal = true;
        }
    }
}

// ============================================================================
// MEMORY FUNCTIONS
// ============================================================================

void CalculatorMode::handleMemoryAdd() {
    memoryValue += currentValue;
    updateDisplay();
}

void CalculatorMode::handleMemorySubtract() {
    memoryValue -= currentValue;
    updateDisplay();
}

void CalculatorMode::handleMemoryRecall() {
    currentValue = memoryValue;
    formatNumber(currentValue, displayBuffer, sizeof(displayBuffer));
    state = CALC_STATE_RESULT_DISPLAYED;
    updateDisplay();
}

void CalculatorMode::handleMemoryClear() {
    memoryValue = 0.0;
    updateDisplay();
}

// ============================================================================
// ✅ FIXED: DISPLAY RENDERING
// ============================================================================

void CalculatorMode::updateDisplay() {
    display.clear(COLOR_BLACK);
    
    // Title
    display.drawText(80, 10, "CALCULATOR", COLOR_WHITE, 2);
    
    // Main display (large numbers)
    display.drawRect(10, 35, 300, 35, COLOR_WHITE);
    display.drawText(15, 42, displayBuffer, COLOR_WHITE, 3);
    
    // Expression (smaller)
    if (strlen(expressionBuffer) > 0) {
        display.drawText(10, 80, expressionBuffer, COLOR_GRAY, 1);
    }
    
    // Memory indicator
    if (memoryValue != 0.0) {
        char memStr[20];
        snprintf(memStr, 20, "M=%.1f", memoryValue);
        display.drawText(10, 100, memStr, COLOR_YELLOW, 1);
    }
    
    // Key guide
    display.drawText(10, 130, "FN:← OK:= +−×÷ *.- M+", COLOR_WHITE, 1);
    
    display.flush();
}

// ============================================================================
// CALCULATION ENGINE (unchanged)
// ============================================================================

void CalculatorMode::calculate() {
    if (currentOperator == OP_NONE) return;
    
    double result = performOperation(storedValue, currentValue, currentOperator);
    
    if (!isValidNumber(result)) {
        setError("ERROR");
        return;
    }
    
    currentValue = result;
    storedValue = result;
    formatNumber(result, displayBuffer, sizeof(displayBuffer));
}

double CalculatorMode::performOperation(double a, double b, CalculatorOperator op) {
    switch (op) {
        case OP_ADD: return a + b;
        case OP_SUBTRACT: return a - b;
        case OP_MULTIPLY: return a * b;
        case OP_DIVIDE: return (fabs(b) < 1e-10) ? NAN : a / b;
        case OP_POWER: return pow(a, b);
        default: return a;
    }
}

void CalculatorMode::setError(const char* message) {
    strcpy(displayBuffer, message);
    state = CALC_STATE_ERROR;
    currentOperator = OP_NONE;
}

void CalculatorMode::formatNumber(double value, char* buffer, uint8_t maxLen) {
    if (isnan(value)) {
        strcpy(buffer, "ERROR");
    } else if (isinf(value)) {
        strcpy(buffer, value > 0 ? "INF" : "-INF");
    } else if (fabs(value) < 1e-10) {
        strcpy(buffer, "0");
    } else if (fabs(value) > 9999999999.0) {
        snprintf(buffer, maxLen, "%.3e", value);
    } else {
        snprintf(buffer, maxLen, "%.10g", value);
    }
    
    if (strlen(buffer) > MAX_DISPLAY_LENGTH) {
        snprintf(buffer, maxLen, "%.2e", value);
    }
}

bool CalculatorMode::isValidNumber(double value) {
    return !isnan(value) && !isinf(value);
}

// ============================================================================
// HISTORY FUNCTIONS (unchanged)
// ============================================================================

void CalculatorMode::addToHistory(const char* expr, double result) {
    if (historyCount < MAX_HISTORY_ENTRIES) {
        historyIndex = historyCount++;
    } else {
        for (uint8_t i = 0; i < MAX_HISTORY_ENTRIES - 1; i++) {
            history[i] = history[i + 1];
        }
        historyIndex = MAX_HISTORY_ENTRIES - 1;
    }
    
    strncpy(history[historyIndex].expression, expr, MAX_EXPRESSION_LENGTH - 1);
    history[historyIndex].result = result;
    history[historyIndex].timestamp = millis();
}

CalculatorHistory* CalculatorMode::getHistory(uint8_t index) {
    if (index < historyCount) return &history[index];
    return nullptr;
}

uint8_t CalculatorMode::getHistoryCount() { return historyCount; }

void CalculatorMode::clearHistory() {
    historyCount = 0;
    memset(history, 0, sizeof(history));
}

void CalculatorMode::generateFakeHistory() {
    const char* fakeCalculations[] = {
        "45 + 23 = 68", "156 - 89 = 67", "12 × 8 = 96", "144 ÷ 12 = 12"
    };
    double fakeResults[] = {68, 67, 96, 12};
    
    clearHistory();
    for (uint8_t i = 0; i < 4 && i < MAX_HISTORY_ENTRIES; i++) {
        addToHistory(fakeCalculations[i], fakeResults[i]);
    }
}

const char* CalculatorMode::getDisplayText() { return displayBuffer; }
double CalculatorMode::getCurrentValue() { return currentValue; }
CalculatorState CalculatorMode::getState() { return state; }
