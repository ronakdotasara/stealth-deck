/**
 * ============================================================================
 * @file keypad.h
 * @brief 5×4 Matrix Keypad Driver with Advanced Input Detection
 * @version 1.0.0
 * @date 2025-11-24
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Advanced keypad driver for the Stealth Deck 5×4 matrix keypad providing:
 * 
 * - Hardware debouncing with configurable timing
 * - Multi-press detection (short press, long press, double-click)
 * - Key combination detection (FN + key)
 * - Circular buffer queue for key events
 * - Interrupt-driven or polling-based scanning
 * - T9 text entry mode support
 * - Ghost key prevention
 * - Key repeat functionality
 * 
 * ============================================================================
 * KEYPAD LAYOUT:
 * 
 *     Col1  Col2  Col3  Col4
 *     ┌────┬────┬────┬────┐
 * Row1│ 1  │ 2  │ 3  │ ↑  │
 *     ├────┼────┼────┼────┤
 * Row2│ 4  │ 5  │ 6  │ ↓  │
 *     ├────┼────┼────┼────┤
 * Row3│ 7  │ 8  │ 9  │ OK │
 *     ├────┼────┼────┼────┤
 * Row4│ *  │ 0  │ #  │ ←  │
 *     ├────┼────┼────┼────┤
 * Row5│ FN │ +  │ -  │FIX │
 *     └────┴────┴────┴────┘
 * 
 * ============================================================================
 * PIN CONNECTIONS:
 * 
 * Rows (Output pins - Active LOW):
 *   Row 1 → GPIO 13
 *   Row 2 → GPIO 12
 *   Row 3 → GPIO 14
 *   Row 4 → GPIO 27
 *   Row 5 → GPIO 26
 * 
 * Columns (Input pins - Internal PULLUP):
 *   Col 1 → GPIO 25
 *   Col 2 → GPIO 33
 *   Col 3 → GPIO 32
 *   Col 4 → GPIO 35
 * 
 * ============================================================================
 * SCANNING ALGORITHM:
 * 
 * 1. Set all row pins HIGH (inactive)
 * 2. For each row:
 *    a. Set row pin LOW (active)
 *    b. Read all column pins
 *    c. If column is LOW, key at (row, col) is pressed
 *    d. Set row pin HIGH again
 * 3. Process detected keys through debouncing
 * 4. Generate key events for state changes
 * 5. Repeat at scan interval (default: 10ms)
 * 
 * ============================================================================
 * KEY EVENT TYPES:
 * 
 * KEY_EVENT_PRESS        - Key pressed down
 * KEY_EVENT_RELEASE      - Key released
 * KEY_EVENT_LONG_PRESS   - Key held > 1 second
 * KEY_EVENT_DOUBLE_CLICK - Key pressed twice within 300ms
 * KEY_EVENT_REPEAT       - Key auto-repeat while held
 * 
 * ============================================================================
 * DEBOUNCING:
 * 
 * Physical switches generate electrical noise when pressed/released.
 * Debouncing eliminates false triggers by:
 * 
 * 1. Sampling key state at regular intervals (10ms)
 * 2. Confirming stable state for minimum duration (20ms)
 * 3. Only generating events after stable confirmation
 * 
 * ============================================================================
 * KEY COMBINATIONS:
 * 
 * FN Key Combinations:
 *   FN + 1 → WiFi Sniffer
 *   FN + 2 → Clipboard
 *   FN + 3 → Notes
 *   FN + 4 → Brightness
 *   FN + 5 → [Part of unlock sequence]
 *   FN + 9 → P2P Mode
 *   FN + FIX → PANIC MODE
 * 
 * ============================================================================
 * T9 TEXT ENTRY:
 * 
 * Multi-tap text entry mode:
 *   2: ABC    3: DEF    4: GHI
 *   5: JKL    6: MNO    7: PQRS
 *   8: TUV    9: WXYZ   0: Space
 *   *: Symbols (#,@,$,etc)
 *   #: Toggle upper/lower case
 * 
 * Example: To type "HELLO"
 *   4(tap twice)=H, 3(tap twice)=E, 5(tap 3 times)=L, 5(tap 3 times)=L, 
 *   6(tap 3 times)=O
 * 
 * ============================================================================
 * GHOST KEY PREVENTION:
 * 
 * Matrix keypads can detect "ghost keys" when multiple keys are pressed:
 * 
 * If keys at (R1,C1), (R1,C2), and (R2,C1) are pressed, the matrix
 * may falsely detect (R2,C2) due to electrical cross-talk.
 * 
 * Prevention: Limit simultaneous key detection to 2 keys (N-key rollover)
 * 
 * ============================================================================
 * MEMORY USAGE:
 * 
 * Key state array: 20 bytes (5 rows × 4 cols)
 * Event queue: 512 bytes (32 events × 16 bytes per event)
 * Debounce timers: 80 bytes (20 keys × 4 bytes)
 * Total: ~600 bytes
 * 
 * ============================================================================
 * PERFORMANCE:
 * 
 * Scan Rate: 100 Hz (10ms interval)
 * Debounce Time: 20ms (2 scans)
 * Long Press Time: 1000ms (100 scans)
 * Double Click Window: 300ms (30 scans)
 * Max Simultaneous Keys: 2 (with ghost prevention)
 * 
 * ============================================================================
 * USAGE EXAMPLE:
 * 
 * ```
 * Keypad keypad;
 * 
 * void setup() {
 *     keypad.begin();
 *     keypad.setDebounceTime(20);
 *     keypad.setLongPressTime(1000);
 * }
 * 
 * void loop() {
 *     if (keypad.available()) {
 *         KeyEvent event = keypad.read();
 *         
 *         if (event.type == KEY_EVENT_PRESS) {
 *             Serial.printf("Key pressed: 0x%02X\n", event.key);
 *         }
 *     }
 * }
 * ```
 * 
 * ============================================================================
 */

#ifndef KEYPAD_H
#define KEYPAD_H

#include <Arduino.h>
#include "../config.h"

// ============================================================================
// CONSTANTS
// ============================================================================

// Keypad dimensions
#define KEYPAD_ROWS 5
#define KEYPAD_COLS 4
#define KEYPAD_TOTAL_KEYS (KEYPAD_ROWS * KEYPAD_COLS)

// Key event types
#define KEY_EVENT_NONE         0
#define KEY_EVENT_PRESS        1
#define KEY_EVENT_RELEASE      2
#define KEY_EVENT_LONG_PRESS   3
#define KEY_EVENT_DOUBLE_CLICK 4
#define KEY_EVENT_REPEAT       5

// Timing defaults (milliseconds)
#define DEFAULT_DEBOUNCE_TIME      20
#define DEFAULT_LONG_PRESS_TIME    1000
#define DEFAULT_DOUBLE_CLICK_TIME  300
#define DEFAULT_REPEAT_DELAY       500
#define DEFAULT_REPEAT_RATE        100
#define DEFAULT_SCAN_INTERVAL      10

// Event queue
#define KEY_EVENT_QUEUE_SIZE 32

// Key states
#define KEY_STATE_IDLE           0
#define KEY_STATE_DEBOUNCING     1
#define KEY_STATE_PRESSED        2
#define KEY_STATE_LONG_PRESSED   3
#define KEY_STATE_RELEASED       4
#define KEY_STATE_WAIT_DOUBLE    5

// Special key codes (defined in config.h)
// KEY_1 through KEY_9, KEY_0, KEY_STAR, KEY_HASH
// KEY_UP, KEY_DOWN, KEY_OK, KEY_BACK
// KEY_FN, KEY_PLUS, KEY_MINUS, KEY_FIX

// Key code for "no key"
#define KEY_NONE 0xFF

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * @struct KeyEvent
 * @brief Structure representing a key event
 */
struct KeyEvent {
    uint8_t key;            // Key code
    uint8_t type;           // Event type (press, release, etc.)
    uint8_t row;            // Physical row (0-4)
    uint8_t col;            // Physical column (0-3)
    unsigned long timestamp; // Event timestamp (millis)
    uint8_t repeatCount;    // Repeat counter for auto-repeat
    
    KeyEvent() : key(KEY_NONE), type(KEY_EVENT_NONE), row(0), col(0), 
                 timestamp(0), repeatCount(0) {}
};

/**
 * @struct KeyState
 * @brief Internal structure tracking key state
 */
struct KeyState {
    uint8_t state;              // Current state
    unsigned long pressTime;    // Time when key was pressed
    unsigned long releaseTime;  // Time when key was released
    unsigned long lastEventTime; // Time of last event
    uint8_t debounceCount;      // Debounce counter
    uint8_t repeatCount;        // Auto-repeat counter
    bool wasDoubleClick;        // Flag to prevent triple-click
};

// ============================================================================
// CLASS DEFINITION
// ============================================================================

/**
 * @class Keypad
 * @brief Advanced matrix keypad driver with multi-press detection
 */
class Keypad {
public:
    // ========================================================================
    // CONSTRUCTOR & DESTRUCTOR
    // ========================================================================
    
    /**
     * @brief Constructor
     */
    Keypad();
    
    /**
     * @brief Destructor
     */
    ~Keypad();

    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    /**
     * @brief Initialize keypad driver
     * 
     * Sets up GPIO pins and starts scanning task.
     * 
     * @return true if successful, false on error
     */
    bool begin();
    
    /**
     * @brief Stop keypad scanning
     */
    void end();
    
    /**
     * @brief Check if keypad is initialized
     * 
     * @return true if initialized
     */
    bool isInitialized() const { return _initialized; }

    // ========================================================================
    // CONFIGURATION
    // ========================================================================
    
    /**
     * @brief Set debounce time
     * 
     * @param ms Debounce time in milliseconds (default: 20)
     */
    void setDebounceTime(uint16_t ms) { _debounceTime = ms; }
    
    /**
     * @brief Set long press time
     * 
     * @param ms Long press time in milliseconds (default: 1000)
     */
    void setLongPressTime(uint16_t ms) { _longPressTime = ms; }
    
    /**
     * @brief Set double-click time window
     * 
     * @param ms Double-click window in milliseconds (default: 300)
     */
    void setDoubleClickTime(uint16_t ms) { _doubleClickTime = ms; }
    
    /**
     * @brief Enable/disable auto-repeat
     * 
     * @param enable true to enable, false to disable
     */
    void setAutoRepeat(bool enable) { _autoRepeatEnabled = enable; }
    
    /**
     * @brief Set auto-repeat timing
     * 
     * @param delay Initial delay before repeat starts (ms)
     * @param rate Repeat rate (ms between repeats)
     */
    void setRepeatTiming(uint16_t delay, uint16_t rate) {
        _repeatDelay = delay;
        _repeatRate = rate;
    }
    
    /**
     * @brief Set scan interval
     * 
     * @param ms Scan interval in milliseconds (default: 10)
     */
    void setScanInterval(uint16_t ms) { _scanInterval = ms; }

    // ========================================================================
    // EVENT READING
    // ========================================================================
    
    /**
     * @brief Check if key events are available
     * 
     * @return true if events are in queue
     */
    bool available() const { return (_eventQueueHead != _eventQueueTail); }
    
    /**
     * @brief Read next key event from queue
     * 
     * @return Key event (or empty event if queue is empty)
     */
    KeyEvent read();
    
    /**
     * @brief Peek at next event without removing it
     * 
     * @return Key event (or empty event if queue is empty)
     */
    KeyEvent peek() const;
    
    /**
     * @brief Clear event queue
     */
    void clearQueue();
    
    /**
     * @brief Get number of events in queue
     * 
     * @return Event count
     */
    uint8_t getEventCount() const;

    // ========================================================================
    // KEY STATE QUERIES
    // ========================================================================
    
    /**
     * @brief Check if a specific key is currently pressed
     * 
     * @param key Key code to check
     * @return true if pressed
     */
    bool isPressed(uint8_t key) const;
    
    /**
     * @brief Check if any key is currently pressed
     * 
     * @return true if any key is pressed
     */
    bool isAnyKeyPressed() const;
    
    /**
     * @brief Get currently pressed keys
     * 
     * @param keys Output array (must hold at least KEYPAD_TOTAL_KEYS bytes)
     * @return Number of keys currently pressed
     */
    uint8_t getPressedKeys(uint8_t* keys) const;
    
    /**
     * @brief Check if FN key is pressed
     * 
     * @return true if FN is pressed
     */
    bool isFNPressed() const { return isPressed(KEY_FN); }
    
    /**
     * @brief Check if two keys are pressed simultaneously (combo)
     * 
     * @param key1 First key
     * @param key2 Second key
     * @return true if both keys are pressed
     */
    bool isComboPressed(uint8_t key1, uint8_t key2) const;

    // ========================================================================
    // SCANNING CONTROL
    // ========================================================================
    
    /**
     * @brief Manually trigger a keypad scan
     * 
     * Useful when not using interrupt-driven scanning.
     */
    void scan();
    
    /**
     * @brief Enable/disable scanning
     * 
     * @param enable true to enable, false to disable
     */
    void enableScanning(bool enable) { _scanningEnabled = enable; }
    
    /**
     * @brief Check if scanning is enabled
     * 
     * @return true if scanning is enabled
     */
    bool isScanningEnabled() const { return _scanningEnabled; }

    // ========================================================================
    // STATISTICS & DEBUG
    // ========================================================================
    
    /**
     * @brief Get total key presses since initialization
     * 
     * @return Total key press count
     */
    uint32_t getTotalKeyPresses() const { return _totalKeyPresses; }
    
    /**
     * @brief Get scan rate (scans per second)
     * 
     * @return Current scan rate
     */
    float getScanRate() const { return _scanRate; }
    
    /**
     * @brief Print keypad statistics to serial
     */
    void printStats() const;
    
    /**
     * @brief Print current key states (debug)
     */
    void printKeyStates() const;

    // ========================================================================
    // T9 TEXT ENTRY SUPPORT
    // ========================================================================
    
    /**
     * @brief Get T9 character for key and tap count
     * 
     * @param key Key code (2-9)
     * @param tapCount Tap count (0-based)
     * @param uppercase true for uppercase
     * @return Character, or 0 if invalid
     */
    static char getT9Char(uint8_t key, uint8_t tapCount, bool uppercase);
    
    /**
     * @brief Get number of T9 characters for a key
     * 
     * @param key Key code (2-9)
     * @return Character count
     */
    static uint8_t getT9CharCount(uint8_t key);

private:
    // ========================================================================
    // PRIVATE MEMBERS
    // ========================================================================
    
    // Hardware configuration
    uint8_t _rowPins[KEYPAD_ROWS];
    uint8_t _colPins[KEYPAD_COLS];
    
    // Key mapping (row, col) -> key code
    uint8_t _keyMap[KEYPAD_ROWS][KEYPAD_COLS];
    
    // Key states
    KeyState _keyStates[KEYPAD_TOTAL_KEYS];
    bool _currentKeyState[KEYPAD_TOTAL_KEYS];  // Current physical state
    bool _lastKeyState[KEYPAD_TOTAL_KEYS];     // Previous scan state
    
    // Event queue (circular buffer)
    KeyEvent _eventQueue[KEY_EVENT_QUEUE_SIZE];
    volatile uint8_t _eventQueueHead;
    volatile uint8_t _eventQueueTail;
    
    // Configuration
    uint16_t _debounceTime;
    uint16_t _longPressTime;
    uint16_t _doubleClickTime;
    uint16_t _repeatDelay;
    uint16_t _repeatRate;
    uint16_t _scanInterval;
    bool _autoRepeatEnabled;
    bool _scanningEnabled;
    bool _initialized;
    
    // Timing
    unsigned long _lastScanTime;
    unsigned long _scanCount;
    unsigned long _lastStatsTime;
    float _scanRate;
    
    // Statistics
    uint32_t _totalKeyPresses;
    uint32_t _totalKeyReleases;
    uint32_t _totalLongPresses;
    uint32_t _totalDoubleClicks;
    
    // Task handle for scanning task (optional)
    TaskHandle_t _scanTaskHandle;
    
    // ========================================================================
    // PRIVATE METHODS
    // ========================================================================
    
    /**
     * @brief Initialize GPIO pins
     */
    void initPins();
    
    /**
     * @brief Initialize key mapping
     */
    void initKeyMap();
    
    /**
     * @brief Scan keypad matrix
     * 
     * Reads all keys and updates physical state array.
     */
    void scanMatrix();
    
    /**
     * @brief Process key states and generate events
     */
    void processKeys();
    
    /**
     * @brief Process a single key
     * 
     * @param index Key index (0-19)
     */
    void processKey(uint8_t index);
    
    /**
     * @brief Add event to queue
     * 
     * @param event Event to add
     * @return true if added, false if queue is full
     */
    bool addEvent(const KeyEvent& event);
    
    /**
     * @brief Get key index from row and column
     * 
     * @param row Row (0-4)
     * @param col Column (0-3)
     * @return Key index (0-19)
     */
    uint8_t getKeyIndex(uint8_t row, uint8_t col) const {
        return row * KEYPAD_COLS + col;
    }
    
    /**
     * @brief Get key code from row and column
     * 
     * @param row Row (0-4)
     * @param col Column (0-3)
     * @return Key code
     */
    uint8_t getKeyCode(uint8_t row, uint8_t col) const {
        return _keyMap[row][col];
    }
    
    /**
     * @brief Update scan rate statistics
     */
    void updateScanRate();
    
    /**
     * @brief Static task function for scanning (FreeRTOS)
     * 
     * @param parameter Pointer to Keypad instance
     */
    static void scanTask(void* parameter);
};

// ============================================================================
// T9 CHARACTER MAPPING (for reference)
// ============================================================================

// T9 key mapping:
// 2: ABC    3: DEF    4: GHI
// 5: JKL    6: MNO    7: PQRS
// 8: TUV    9: WXYZ   0: Space
// *: Symbols  #: Mode toggle

#endif // KEYPAD_H

// ============================================================================
// END OF FILE
// ============================================================================
