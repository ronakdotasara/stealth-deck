/**
 * ============================================================================
 * @file keypad.h
 * @brief 5×4 Matrix Keypad Driver with Advanced Input Detection
 * @version 1.0.0
 * @date 2025-11-30
 * @author Stealth Deck Project
 * @license MIT
 * ============================================================================
 */

#ifndef KEYPAD_H
#define KEYPAD_H

#include <Arduino.h>
#include "config.h"  // ← KeyEvent is NOW defined here only!

// ============================================================================
// CONSTANTS
// ============================================================================

#define KEYPAD_TOTAL_KEYS (KEYPAD_ROWS * KEYPAD_COLS)
#define KEY_EVENT_NONE         0
#define KEY_EVENT_PRESS        1
#define KEY_EVENT_RELEASE      2
#define KEY_EVENT_LONG_PRESS   3
#define KEY_EVENT_DOUBLE_CLICK 4
#define KEY_EVENT_REPEAT       5

#define DEFAULT_DEBOUNCE_TIME      20
#define DEFAULT_LONG_PRESS_TIME    1000
#define DEFAULT_DOUBLE_CLICK_TIME  300
#define DEFAULT_REPEAT_DELAY       500
#define DEFAULT_REPEAT_RATE        100
#define DEFAULT_SCAN_INTERVAL      10
#define KEY_EVENT_QUEUE_SIZE       32

#define KEYPAD_STATE_IDLE           0
#define KEYPAD_STATE_DEBOUNCING     1
#define KEYPAD_STATE_PRESSED        2
#define KEYPAD_STATE_LONG_PRESSED   3
#define KEYPAD_STATE_RELEASED       4
#define KEYPAD_STATE_WAIT_DOUBLE    5
#define KEYPAD_KEY_NONE             0xFF

// ============================================================================
// TYPE DEFINITIONS (KeyEvent REMOVED - now in config.h)
// ============================================================================

struct KeyState {
    uint8_t state;              // Current state
    unsigned long pressTime;    // Time when key was pressed
    unsigned long releaseTime;  // Time when key was released
    unsigned long lastEventTime;// Time of last event
    uint8_t debounceCount;      // Debounce counter
    uint8_t repeatCount;        // Auto-repeat counter
    bool wasDoubleClick;        // Flag to prevent triple-click
};

// ============================================================================
// CLASS DEFINITION
// ============================================================================

class Keypad {
public:
    Keypad();
    ~Keypad();

    bool begin();
    void end();
    bool isInitialized() const { return _initialized; }

    void setDebounceTime(uint16_t ms) { _debounceTime = ms; }
    void setLongPressTime(uint16_t ms) { _longPressTime = ms; }
    void setDoubleClickTime(uint16_t ms) { _doubleClickTime = ms; }
    void setAutoRepeat(bool enable) { _autoRepeatEnabled = enable; }
    void setRepeatTiming(uint16_t delay, uint16_t rate) {
        _repeatDelay = delay;
        _repeatRate = rate;
    }
    void setScanInterval(uint16_t ms) { _scanInterval = ms; }

    bool available() const { return (_eventQueueHead != _eventQueueTail); }
    KeyEvent read();
    KeyEvent peek() const;
    void clearQueue();
    uint8_t getEventCount() const;

    bool isPressed(uint8_t key) const;
    bool isAnyKeyPressed() const;
    uint8_t getPressedKeys(uint8_t* keys) const;
    bool isFNPressed() const { return isPressed(KEY_FN); }
    bool isComboPressed(uint8_t key1, uint8_t key2) const;

    void scan();
    void enableScanning(bool enable) { _scanningEnabled = enable; }
    bool isScanningEnabled() const { return _scanningEnabled; }

    uint32_t getTotalKeyPresses() const { return _totalKeyPresses; }
    float getScanRate() const { return _scanRate; }
    void printStats() const;
    void printKeyStates() const;

    static char getT9Char(uint8_t key, uint8_t tapCount, bool uppercase);
    static uint8_t getT9CharCount(uint8_t key);

private:
    uint8_t _rowPins[KEYPAD_ROWS];
    uint8_t _colPins[KEYPAD_COLS];
    uint8_t _keyMap[KEYPAD_ROWS][KEYPAD_COLS];
    KeyState _keyStates[KEYPAD_TOTAL_KEYS];
    bool _currentKeyState[KEYPAD_TOTAL_KEYS];
    bool _lastKeyState[KEYPAD_TOTAL_KEYS];
    
    KeyEvent _eventQueue[KEY_EVENT_QUEUE_SIZE];
    volatile uint8_t _eventQueueHead;
    volatile uint8_t _eventQueueTail;
    
    uint16_t _debounceTime;
    uint16_t _longPressTime;
    uint16_t _doubleClickTime;
    uint16_t _repeatDelay;
    uint16_t _repeatRate;
    uint16_t _scanInterval;
    bool _autoRepeatEnabled;
    bool _scanningEnabled;
    bool _initialized;
    
    unsigned long _lastScanTime;
    unsigned long _scanCount;
    unsigned long _lastStatsTime;
    float _scanRate;
    uint32_t _totalKeyPresses;
    uint32_t _totalKeyReleases;
    uint32_t _totalLongPresses;
    uint32_t _totalDoubleClicks;
    TaskHandle_t _scanTaskHandle;

    void initPins();
    void initKeyMap();
    void scanMatrix();
    void processKeys();
    void processKey(uint8_t index);
    bool addEvent(const KeyEvent& event);
    uint8_t getKeyIndex(uint8_t row, uint8_t col) const {
        return row * KEYPAD_COLS + col;
    }
    uint8_t getKeyCode(uint8_t row, uint8_t col) const {
        return _keyMap[row][col];
    }
    void updateScanRate();
    static void scanTask(void* parameter);
};

#endif // KEYPAD_H
