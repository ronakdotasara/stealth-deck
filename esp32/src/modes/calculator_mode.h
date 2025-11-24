/**
 * ============================================================================
 * calculator_mode.h - Calculator Mode for Stealth Deck
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-24
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Calculator mode implementation providing stealth cover for the device.
 * Implements a fully functional calculator with history to appear legitimate.
 * 
 * Features:
 * - Basic arithmetic operations (+, -, *, /)
 * - Advanced functions (sin, cos, tan, sqrt, pow)
 * - Memory functions (M+, M-, MR, MC)
 * - Calculation history
 * - Fake history generation for panic mode
 * - Scientific notation support
 * 
 * ============================================================================
 */

#ifndef CALCULATOR_MODE_H
#define CALCULATOR_MODE_H

#include <Arduino.h>

#define MAX_DISPLAY_LENGTH 16
#define MAX_HISTORY_ENTRIES 20
#define MAX_EXPRESSION_LENGTH 64

enum CalculatorState {
    CALC_STATE_IDLE,
    CALC_STATE_ENTERING_NUMBER,
    CALC_STATE_ENTERING_OPERATOR,
    CALC_STATE_RESULT_DISPLAYED,
    CALC_STATE_ERROR
};

enum CalculatorOperator {
    OP_NONE,
    OP_ADD,
    OP_SUBTRACT,
    OP_MULTIPLY,
    OP_DIVIDE,
    OP_POWER,
    OP_SQRT,
    OP_SIN,
    OP_COS,
    OP_TAN
};

struct CalculatorHistory {
    char expression[MAX_EXPRESSION_LENGTH];
    double result;
    unsigned long timestamp;
};

class CalculatorMode {
public:
    CalculatorMode();
    
    void begin();
    void reset();
    
    void handleKey(uint8_t key);
    void handleDigit(uint8_t digit);
    void handleOperator(CalculatorOperator op);
    void handleEquals();
    void handleClear();
    void handleBackspace();
    void handleDecimal();
    
    void handleMemoryAdd();
    void handleMemorySubtract();
    void handleMemoryRecall();
    void handleMemoryClear();
    
    const char* getDisplayText();
    double getCurrentValue();
    CalculatorState getState();
    
    void addToHistory(const char* expr, double result);
    CalculatorHistory* getHistory(uint8_t index);
    uint8_t getHistoryCount();
    void clearHistory();
    
    void generateFakeHistory();
    
private:
    char displayBuffer[MAX_DISPLAY_LENGTH + 1];
    char expressionBuffer[MAX_EXPRESSION_LENGTH];
    
    double currentValue;
    double storedValue;
    double memoryValue;
    
    CalculatorOperator currentOperator;
    CalculatorState state;
    
    bool hasDecimal;
    uint8_t decimalPlaces;
    
    CalculatorHistory history[MAX_HISTORY_ENTRIES];
    uint8_t historyCount;
    uint8_t historyIndex;
    
    void updateDisplay();
    void calculate();
    void setError(const char* message);
    void formatNumber(double value, char* buffer, uint8_t maxLen);
    bool isValidNumber(double value);
    
    double performOperation(double a, double b, CalculatorOperator op);
    double performUnaryOperation(double a, CalculatorOperator op);
};

#endif

