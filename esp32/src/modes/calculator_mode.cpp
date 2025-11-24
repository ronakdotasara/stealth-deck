/**
 * ============================================================================
 * calculator_mode.cpp - Calculator Mode Implementation
 * ============================================================================
 */

#include "calculator_mode.h"
#include <math.h>

CalculatorMode::CalculatorMode() {
    reset();
}

void CalculatorMode::begin() {
    reset();
    generateFakeHistory();
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

void CalculatorMode::handleKey(uint8_t key) {
    if (key >= '0' && key <= '9') {
        handleDigit(key - '0');
    } else {
        switch (key) {
            case '+':
                handleOperator(OP_ADD);
                break;
            case '-':
                handleOperator(OP_SUBTRACT);
                break;
            case '*':
                handleOperator(OP_MULTIPLY);
                break;
            case '/':
                handleOperator(OP_DIVIDE);
                break;
            case '=':
                handleEquals();
                break;
            case 'C':
                handleClear();
                break;
            case '.':
                handleDecimal();
                break;
            case 'B':
                handleBackspace();
                break;
        }
    }
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
        if (hasDecimal) {
            decimalPlaces++;
        }
        
        char digitStr[2];
        digitStr[0] = '0' + digit;
        digitStr[1] = '\0';
        strcat(displayBuffer, digitStr);
        
        currentValue = atof(displayBuffer);
        updateDisplay();
    }
}

void CalculatorMode::handleOperator(CalculatorOperator op) {
    if (state == CALC_STATE_ENTERING_NUMBER) {
        if (currentOperator != OP_NONE) {
            calculate();
        } else {
            storedValue = currentValue;
        }
    }
    
    currentOperator = op;
    state = CALC_STATE_ENTERING_OPERATOR;
    hasDecimal = false;
    decimalPlaces = 0;
    
    char opStr[8];
    switch (op) {
        case OP_ADD: strcpy(opStr, " + "); break;
        case OP_SUBTRACT: strcpy(opStr, " - "); break;
        case OP_MULTIPLY: strcpy(opStr, " × "); break;
        case OP_DIVIDE: strcpy(opStr, " ÷ "); break;
        case OP_POWER: strcpy(opStr, " ^ "); break;
        default: strcpy(opStr, " "); break;
    }
    
    if (strlen(expressionBuffer) + strlen(displayBuffer) + strlen(opStr) < MAX_EXPRESSION_LENGTH) {
        strcat(expressionBuffer, displayBuffer);
        strcat(expressionBuffer, opStr);
    }
}

void CalculatorMode::handleEquals() {
    if (state == CALC_STATE_ENTERING_NUMBER && currentOperator != OP_NONE) {
        calculate();
        
        char resultStr[32];
        formatNumber(currentValue, resultStr, sizeof(resultStr));
        
        if (strlen(expressionBuffer) + strlen(displayBuffer) + 4 < MAX_EXPRESSION_LENGTH) {
            strcat(expressionBuffer, displayBuffer);
            strcat(expressionBuffer, " = ");
            strcat(expressionBuffer, resultStr);
        }
        
        addToHistory(expressionBuffer, currentValue);
        
        strcpy(displayBuffer, resultStr);
        currentValue = atof(displayBuffer);
        
        state = CALC_STATE_RESULT_DISPLAYED;
        currentOperator = OP_NONE;
        storedValue = 0.0;
        memset(expressionBuffer, 0, sizeof(expressionBuffer));
        hasDecimal = false;
        decimalPlaces = 0;
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
            updateDisplay();
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
            updateDisplay();
        }
    }
}

void CalculatorMode::handleMemoryAdd() {
    memoryValue += currentValue;
}

void CalculatorMode::handleMemorySubtract() {
    memoryValue -= currentValue;
}

void CalculatorMode::handleMemoryRecall() {
    currentValue = memoryValue;
    formatNumber(currentValue, displayBuffer, sizeof(displayBuffer));
    state = CALC_STATE_RESULT_DISPLAYED;
    updateDisplay();
}

void CalculatorMode::handleMemoryClear() {
    memoryValue = 0.0;
}

const char* CalculatorMode::getDisplayText() {
    return displayBuffer;
}

double CalculatorMode::getCurrentValue() {
    return currentValue;
}

CalculatorState CalculatorMode::getState() {
    return state;
}

void CalculatorMode::calculate() {
    if (currentOperator == OP_NONE) {
        return;
    }
    
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
        case OP_ADD:
            return a + b;
        case OP_SUBTRACT:
            return a - b;
        case OP_MULTIPLY:
            return a * b;
        case OP_DIVIDE:
            if (fabs(b) < 1e-10) {
                return NAN;
            }
            return a / b;
        case OP_POWER:
            return pow(a, b);
        case OP_SQRT:
            return sqrt(a);
        case OP_SIN:
            return sin(a * PI / 180.0);
        case OP_COS:
            return cos(a * PI / 180.0);
        case OP_TAN:
            return tan(a * PI / 180.0);
        default:
            return a;
    }
}

double CalculatorMode::performUnaryOperation(double a, CalculatorOperator op) {
    switch (op) {
        case OP_SQRT:
            if (a < 0) return NAN;
            return sqrt(a);
        case OP_SIN:
            return sin(a * PI / 180.0);
        case OP_COS:
            return cos(a * PI / 180.0);
        case OP_TAN:
            return tan(a * PI / 180.0);
        default:
            return a;
    }
}

void CalculatorMode::updateDisplay() {
    // Display buffer is already updated in handleDigit
}

void CalculatorMode::setError(const char* message) {
    strcpy(displayBuffer, message);
    state = CALC_STATE_ERROR;
    currentOperator = OP_NONE;
}

void CalculatorMode::formatNumber(double value, char* buffer, uint8_t maxLen) {
    if (isnan(value)) {
        strcpy(buffer, "ERROR");
        return;
    }
    
    if (isinf(value)) {
        strcpy(buffer, value > 0 ? "INF" : "-INF");
        return;
    }
    
    if (fabs(value) < 1e-10) {
        strcpy(buffer, "0");
        return;
    }
    
    if (fabs(value) > 9999999999.0 || (fabs(value) < 0.0001 && value != 0)) {
        snprintf(buffer, maxLen, "%.4e", value);
    } else {
        snprintf(buffer, maxLen, "%.8g", value);
    }
    
    if (strlen(buffer) > MAX_DISPLAY_LENGTH) {
        snprintf(buffer, maxLen, "%.2e", value);
    }
}

bool CalculatorMode::isValidNumber(double value) {
    return !isnan(value) && !isinf(value);
}

void CalculatorMode::addToHistory(const char* expr, double result) {
    if (historyCount < MAX_HISTORY_ENTRIES) {
        historyIndex = historyCount;
        historyCount++;
    } else {
        historyIndex = 0;
        for (int i = 0; i < MAX_HISTORY_ENTRIES - 1; i++) {
            history[i] = history[i + 1];
        }
        historyIndex = MAX_HISTORY_ENTRIES - 1;
    }
    
    strncpy(history[historyIndex].expression, expr, MAX_EXPRESSION_LENGTH - 1);
    history[historyIndex].expression[MAX_EXPRESSION_LENGTH - 1] = '\0';
    history[historyIndex].result = result;
    history[historyIndex].timestamp = millis();
}

CalculatorHistory* CalculatorMode::getHistory(uint8_t index) {
    if (index < historyCount) {
        return &history[index];
    }
    return nullptr;
}

uint8_t CalculatorMode::getHistoryCount() {
    return historyCount;
}

void CalculatorMode::clearHistory() {
    historyCount = 0;
    historyIndex = 0;
    memset(history, 0, sizeof(history));
}

void CalculatorMode::generateFakeHistory() {
    const char* fakeCalculations[] = {
        "45 + 23 = 68",
        "156 - 89 = 67",
        "12 × 8 = 96",
        "144 ÷ 12 = 12",
        "25 + 30 = 55",
        "100 - 37 = 63",
        "15 × 4 = 60",
        "81 ÷ 9 = 9",
        "56 + 44 = 100",
        "200 - 125 = 75"
    };
    
    double fakeResults[] = {68, 67, 96, 12, 55, 63, 60, 9, 100, 75};
    
    clearHistory();
    
    unsigned long baseTime = millis() - 3600000;
    
    for (int i = 0; i < 10 && i < MAX_HISTORY_ENTRIES; i++) {
        strncpy(history[i].expression, fakeCalculations[i], MAX_EXPRESSION_LENGTH - 1);
        history[i].result = fakeResults[i];
        history[i].timestamp = baseTime + (i * 360000);
    }
    
    historyCount = 10;
}

