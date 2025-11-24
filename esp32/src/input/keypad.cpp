/**
 * ============================================================================
 * @file keypad.cpp
 * @brief 5×4 Matrix Keypad Driver Implementation
 * @version 1.0.0
 * @date 2025-11-24
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Complete implementation of the advanced matrix keypad driver including:
 * 
 * - Matrix scanning algorithm with row/column iteration
 * - Debouncing state machine for noise elimination
 * - Multi-press event detection (long press, double-click)
 * - Auto-repeat for held keys
 * - Key combination detection
 * - Circular buffer event queue
 * - T9 text entry character mapping
 * - Performance monitoring and statistics
 * 
 * ============================================================================
 * DEBOUNCING STATE MACHINE:
 * 
 * IDLE ──[Press detected]──> DEBOUNCING ──[Stable LOW]──> PRESSED
 *                                │                           │
 *                                │                           │
 *                          [Unstable]                  [Hold > 1s]
 *                                │                           │
 *                                └───────────────────────────┤
 *                                                            ▼
 * RELEASED <──[Stable HIGH]── DEBOUNCING <────────── LONG_PRESSED
 *     │                                                      │
 *     │                                                      │
 *     └──[< 300ms from last press]──> DOUBLE_CLICK          │
 *     │                                                      │
 *     └──────────────────────────────────────────────────────
 * 
 * ============================================================================
 * SCANNING ALGORITHM DETAILS:
 * 
 * The matrix keypad uses 5 row pins (outputs) and 4 column pins (inputs).
 * Columns have internal pull-up resistors, so they normally read HIGH.
 * 
 * Scanning Process:
 * 1. Set all row pins HIGH (inactive)
 * 2. For each row (0-4):
 *    a. Set current row pin LOW (active)
 *    b. Wait 1μs for signal to stabilize
 *    c. Read all column pins (0-3)
 *    d. If column reads LOW, key at (row, col) is pressed
 *    e. Set row pin HIGH again
 * 3. Process detected keys through debouncing
 * 4. Generate events for state changes
 * 
 * ============================================================================
 * GHOST KEY PREVENTION:
 * 
 * When 3 keys form an L-shape, a 4th "ghost" key may be falsely detected:
 * 
 * Example: If (R1,C1), (R1,C2), and (R2,C1) are pressed:
 *   Row1: LOW  → Col1: LOW (real), Col2: LOW (real)
 *   Row2: LOW  → Col1: LOW (real), Col2: LOW (GHOST!)
 * 
 * Prevention: Limit simultaneous keys to 2 (2-key rollover)
 * 
 * ============================================================================
 */

#include "keypad.h"

// Debug logging
#ifdef DEBUG
  #define KEYPAD_DEBUG(x) DEBUG_SERIAL.print("[KEYPAD] "); DEBUG_SERIAL.println(x)
  #define KEYPAD_DEBUGF(format, ...) DEBUG_SERIAL.printf("[KEYPAD] " format "\n", __VA_ARGS__)
#else
  #define KEYPAD_DEBUG(x)
  #define KEYPAD_DEBUGF(format, ...)
#endif

// ============================================================================
// T9 CHARACTER MAPPING
// ============================================================================

// T9 key to character mapping (lowercase)
const char T9_CHARS[][5] = {
    "",         // 0 - Space (handled separately)
    "",         // 1 - Special
    "abc",      // 2
    "def",      // 3
    "ghi",      // 4
    "jkl",      // 5
    "mno",      // 6
    "pqrs",     // 7
    "tuv",      // 8
    "wxyz"      // 9
};

// Symbol map for * key
const char T9_SYMBOLS[] = " .,?!'\"1-()@/:_;+&%*[]{}#¤§|~€£$¥";

// ============================================================================
// CONSTRUCTOR
// ============================================================================

/**
 * @brief Constructor - Initialize member variables
 */
Keypad::Keypad() :
    _eventQueueHead(0),
    _eventQueueTail(0),
    _debounceTime(DEFAULT_DEBOUNCE_TIME),
    _longPressTime(DEFAULT_LONG_PRESS_TIME),
    _doubleClickTime(DEFAULT_DOUBLE_CLICK_TIME),
    _repeatDelay(DEFAULT_REPEAT_DELAY),
    _repeatRate(DEFAULT_REPEAT_RATE),
    _scanInterval(DEFAULT_SCAN_INTERVAL),
    _autoRepeatEnabled(true),
    _scanningEnabled(false),
    _initialized(false),
    _lastScanTime(0),
    _scanCount(0),
    _lastStatsTime(0),
    _scanRate(0.0f),
    _totalKeyPresses(0),
    _totalKeyReleases(0),
    _totalLongPresses(0),
    _totalDoubleClicks(0),
    _scanTaskHandle(nullptr)
{
    // Initialize row pins from config
    _rowPins[0] = KEYPAD_ROW_1;
    _rowPins[1] = KEYPAD_ROW_2;
    _rowPins[2] = KEYPAD_ROW_3;
    _rowPins[3] = KEYPAD_ROW_4;
    _rowPins[4] = KEYPAD_ROW_5;
    
    // Initialize column pins from config
    _colPins[0] = KEYPAD_COL_1;
    _colPins[1] = KEYPAD_COL_2;
    _colPins[2] = KEYPAD_COL_3;
    _colPins[3] = KEYPAD_COL_4;
    
    // Initialize key states
    for (uint8_t i = 0; i < KEYPAD_TOTAL_KEYS; i++) {
        _keyStates[i].state = KEY_STATE_IDLE;
        _keyStates[i].pressTime = 0;
        _keyStates[i].releaseTime = 0;
        _keyStates[i].lastEventTime = 0;
        _keyStates[i].debounceCount = 0;
        _keyStates[i].repeatCount = 0;
        _keyStates[i].wasDoubleClick = false;
        
        _currentKeyState[i] = false;
        _lastKeyState[i] = false;
    }
    
    // Initialize key mapping
    initKeyMap();
}

// ============================================================================
// DESTRUCTOR
// ============================================================================

/**
 * @brief Destructor - Clean up resources
 */
Keypad::~Keypad() {
    end();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * @brief Initialize keypad driver
 * 
 * Sets up GPIO pins, initializes state, and optionally starts scanning task.
 * 
 * @return true if successful
 */
bool Keypad::begin() {
    KEYPAD_DEBUG("Initializing keypad...");
    
    // Initialize GPIO pins
    initPins();
    
    // Clear event queue
    clearQueue();
    
    // Reset timing
    _lastScanTime = millis();
    _lastStatsTime = millis();
    
    // Mark as initialized
    _initialized = true;
    _scanningEnabled = true;
    
    KEYPAD_DEBUG("✓ Keypad initialized");
    KEYPAD_DEBUGF("  Debounce: %dms, Long Press: %dms, Double-Click: %dms", 
                  _debounceTime, _longPressTime, _doubleClickTime);
    
    // Optional: Create FreeRTOS task for automatic scanning
    #ifdef USE_FREERTOS_TASK
    xTaskCreate(
        scanTask,           // Task function
        "KeypadScan",       // Task name
        2048,               // Stack size
        this,               // Parameter (this pointer)
        2,                  // Priority
        &_scanTaskHandle    // Task handle
    );
    KEYPAD_DEBUG("✓ Scanning task created");
    #endif
    
    return true;
}

/**
 * @brief Stop keypad scanning
 */
void Keypad::end() {
    _scanningEnabled = false;
    _initialized = false;
    
    // Delete scanning task if it exists
    if (_scanTaskHandle != nullptr) {
        vTaskDelete(_scanTaskHandle);
        _scanTaskHandle = nullptr;
    }
    
    KEYPAD_DEBUG("Keypad stopped");
}

/**
 * @brief Initialize GPIO pins
 */
void Keypad::initPins() {
    // Configure row pins as outputs (initially HIGH)
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        pinMode(_rowPins[row], OUTPUT);
        digitalWrite(_rowPins[row], HIGH);
    }
    
    // Configure column pins as inputs with pull-up resistors
    for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
        pinMode(_colPins[col], INPUT_PULLUP);
    }
    
    KEYPAD_DEBUG("  ✓ GPIO pins configured");
}

/**
 * @brief Initialize key mapping matrix
 * 
 * Maps physical (row, col) positions to logical key codes.
 */
void Keypad::initKeyMap() {
    // Row 0: 1, 2, 3, UP
    _keyMap[0][0] = KEY_1;
    _keyMap[0][1] = KEY_2;
    _keyMap[0][2] = KEY_3;
    _keyMap[0][3] = KEY_UP;
    
    // Row 1: 4, 5, 6, DOWN
    _keyMap[1][0] = KEY_4;
    _keyMap[1][1] = KEY_5;
    _keyMap[1][2] = KEY_6;
    _keyMap[1][3] = KEY_DOWN;
    
    // Row 2: 7, 8, 9, OK
    _keyMap[2][0] = KEY_7;
    _keyMap[2][1] = KEY_8;
    _keyMap[2][2] = KEY_9;
    _keyMap[2][3] = KEY_OK;
    
    // Row 3: *, 0, #, BACK
    _keyMap[3][0] = KEY_STAR;
    _keyMap[3][1] = KEY_0;
    _keyMap[3][2] = KEY_HASH;
    _keyMap[3][3] = KEY_BACK;
    
    // Row 4: FN, +, -, FIX
    _keyMap[4][0] = KEY_FN;
    _keyMap[4][1] = KEY_PLUS;
    _keyMap[4][2] = KEY_MINUS;
    _keyMap[4][3] = KEY_FIX;
    
    KEYPAD_DEBUG("  ✓ Key mapping initialized");
}

// ============================================================================
// EVENT READING
// ============================================================================

/**
 * @brief Read next key event from queue
 * 
 * @return Key event (or empty event if queue is empty)
 */
KeyEvent Keypad::read() {
    if (!available()) {
        return KeyEvent();  // Return empty event
    }
    
    // Read event from queue
    KeyEvent event = _eventQueue[_eventQueueTail];
    
    // Advance tail pointer (circular buffer)
    _eventQueueTail = (_eventQueueTail + 1) % KEY_EVENT_QUEUE_SIZE;
    
    return event;
}

/**
 * @brief Peek at next event without removing it
 * 
 * @return Key event (or empty event if queue is empty)
 */
KeyEvent Keypad::peek() const {
    if (!available()) {
        return KeyEvent();
    }
    
    return _eventQueue[_eventQueueTail];
}

/**
 * @brief Clear event queue
 */
void Keypad::clearQueue() {
    _eventQueueHead = 0;
    _eventQueueTail = 0;
}

/**
 * @brief Get number of events in queue
 * 
 * @return Event count
 */
uint8_t Keypad::getEventCount() const {
    if (_eventQueueHead >= _eventQueueTail) {
        return _eventQueueHead - _eventQueueTail;
    } else {
        return KEY_EVENT_QUEUE_SIZE - _eventQueueTail + _eventQueueHead;
    }
}

// ============================================================================
// KEY STATE QUERIES
// ============================================================================

/**
 * @brief Check if a specific key is currently pressed
 * 
 * @param key Key code to check
 * @return true if pressed
 */
bool Keypad::isPressed(uint8_t key) const {
    // Search through key map to find matching key code
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
            if (_keyMap[row][col] == key) {
                uint8_t index = getKeyIndex(row, col);
                return _currentKeyState[index];
            }
        }
    }
    return false;
}

/**
 * @brief Check if any key is currently pressed
 * 
 * @return true if any key is pressed
 */
bool Keypad::isAnyKeyPressed() const {
    for (uint8_t i = 0; i < KEYPAD_TOTAL_KEYS; i++) {
        if (_currentKeyState[i]) {
            return true;
        }
    }
    return false;
}

/**
 * @brief Get currently pressed keys
 * 
 * @param keys Output array
 * @return Number of keys currently pressed
 */
uint8_t Keypad::getPressedKeys(uint8_t* keys) const {
    uint8_t count = 0;
    
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
            uint8_t index = getKeyIndex(row, col);
            if (_currentKeyState[index]) {
                keys[count++] = _keyMap[row][col];
            }
        }
    }
    
    return count;
}

/**
 * @brief Check if two keys are pressed simultaneously
 * 
 * @param key1 First key
 * @param key2 Second key
 * @return true if both keys are pressed
 */
bool Keypad::isComboPressed(uint8_t key1, uint8_t key2) const {
    return isPressed(key1) && isPressed(key2);
}

// ============================================================================
// SCANNING
// ============================================================================

/**
 * @brief Manually trigger a keypad scan
 * 
 * This is the main scanning function called either manually or by task.
 */
void Keypad::scan() {
    if (!_initialized || !_scanningEnabled) {
        return;
    }
    
    unsigned long now = millis();
    
    // Check if enough time has passed since last scan
    if (now - _lastScanTime < _scanInterval) {
        return;
    }
    
    _lastScanTime = now;
    _scanCount++;
    
    // Scan the matrix
    scanMatrix();
    
    // Process keys and generate events
    processKeys();
    
    // Update scan rate statistics
    updateScanRate();
}

/**
 * @brief Scan keypad matrix
 * 
 * Reads physical state of all keys in the matrix.
 */
void Keypad::scanMatrix() {
    // Save previous state
    memcpy(_lastKeyState, _currentKeyState, KEYPAD_TOTAL_KEYS);
    
    // Scan each row
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        // Activate current row (set LOW)
        digitalWrite(_rowPins[row], LOW);
        
        // Wait for signal to stabilize (1μs is usually enough)
        delayMicroseconds(1);
        
        // Read all columns
        for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
            uint8_t index = getKeyIndex(row, col);
            
            // Column reads LOW when key is pressed
            _currentKeyState[index] = (digitalRead(_colPins[col]) == LOW);
        }
        
        // Deactivate row (set HIGH)
        digitalWrite(_rowPins[row], HIGH);
    }
    
    // Ghost key prevention: If more than 2 keys pressed, ignore all
    uint8_t pressedCount = 0;
    for (uint8_t i = 0; i < KEYPAD_TOTAL_KEYS; i++) {
        if (_currentKeyState[i]) pressedCount++;
    }
    
    if (pressedCount > 2) {
        // Too many keys pressed simultaneously - likely ghost keys
        // Restore previous state
        memcpy(_currentKeyState, _lastKeyState, KEYPAD_TOTAL_KEYS);
        KEYPAD_DEBUGF("Ghost key prevention: %d keys detected", pressedCount);
    }
}

/**
 * @brief Process all keys and generate events
 */
void Keypad::processKeys() {
    for (uint8_t i = 0; i < KEYPAD_TOTAL_KEYS; i++) {
        processKey(i);
    }
}

/**
 * @brief Process a single key through state machine
 * 
 * @param index Key index (0-19)
 */
void Keypad::processKey(uint8_t index) {
    KeyState& state = _keyStates[index];
    bool currentlyPressed = _currentKeyState[index];
    bool previouslyPressed = _lastKeyState[index];
    unsigned long now = millis();
    
    // Get key code and position
    uint8_t row = index / KEYPAD_COLS;
    uint8_t col = index % KEYPAD_COLS;
    uint8_t keyCode = getKeyCode(row, col);
    
    // ========================================================================
    // STATE MACHINE
    // ========================================================================
    
    switch (state.state) {
        
        // ====================================================================
        // IDLE STATE
        // ====================================================================
        case KEY_STATE_IDLE:
            if (currentlyPressed && !previouslyPressed) {
                // Key press detected - start debouncing
                state.state = KEY_STATE_DEBOUNCING;
                state.pressTime = now;
                state.debounceCount = 1;
                
                KEYPAD_DEBUGF("Key 0x%02X: IDLE -> DEBOUNCING", keyCode);
            }
            break;
        
        // ====================================================================
        // DEBOUNCING STATE
        // ====================================================================
        case KEY_STATE_DEBOUNCING:
            if (currentlyPressed) {
                state.debounceCount++;
                
                // Check if debounce time has passed
                if (now - state.pressTime >= _debounceTime) {
                    // Key is stable - confirmed press
                    state.state = KEY_STATE_PRESSED;
                    state.lastEventTime = now;
                    
                    // Generate PRESS event
                    KeyEvent event;
                    event.key = keyCode;
                    event.type = KEY_EVENT_PRESS;
                    event.row = row;
                    event.col = col;
                    event.timestamp = now;
                    event.repeatCount = 0;
                    addEvent(event);
                    
                    _totalKeyPresses++;
                    
                    KEYPAD_DEBUGF("Key 0x%02X: DEBOUNCING -> PRESSED", keyCode);
                }
            } else {
                // Key released before debounce complete - false trigger
                state.state = KEY_STATE_IDLE;
                state.debounceCount = 0;
                
                KEYPAD_DEBUGF("Key 0x%02X: Bounce rejected", keyCode);
            }
            break;
        
        // ====================================================================
        // PRESSED STATE
        // ====================================================================
        case KEY_STATE_PRESSED:
            if (currentlyPressed) {
                // Check for long press
                if (now - state.pressTime >= _longPressTime) {
                    state.state = KEY_STATE_LONG_PRESSED;
                    
                    // Generate LONG_PRESS event
                    KeyEvent event;
                    event.key = keyCode;
                    event.type = KEY_EVENT_LONG_PRESS;
                    event.row = row;
                    event.col = col;
                    event.timestamp = now;
                    event.repeatCount = 0;
                    addEvent(event);
                    
                    _totalLongPresses++;
                    
                    KEYPAD_DEBUGF("Key 0x%02X: PRESSED -> LONG_PRESSED", keyCode);
                }
                
                // Check for auto-repeat
                if (_autoRepeatEnabled && 
                    now - state.lastEventTime >= _repeatDelay + (state.repeatCount * _repeatRate)) {
                    
                    state.repeatCount++;
                    state.lastEventTime = now;
                    
                    // Generate REPEAT event
                    KeyEvent event;
                    event.key = keyCode;
                    event.type = KEY_EVENT_REPEAT;
                    event.row = row;
                    event.col = col;
                    event.timestamp = now;
                    event.repeatCount = state.repeatCount;
                    addEvent(event);
                    
                    KEYPAD_DEBUGF("Key 0x%02X: REPEAT %d", keyCode, state.repeatCount);
                }
            } else {
                // Key released
                state.state = KEY_STATE_RELEASED;
                state.releaseTime = now;
                state.repeatCount = 0;
            }
            break;
        
        // ====================================================================
        // LONG_PRESSED STATE
        // ====================================================================
        case KEY_STATE_LONG_PRESSED:
            if (!currentlyPressed) {
                // Key released after long press
                state.state = KEY_STATE_RELEASED;
                state.releaseTime = now;
                state.repeatCount = 0;
            }
            break;
        
        // ====================================================================
        // RELEASED STATE
        // ====================================================================
        case KEY_STATE_RELEASED:
            // Generate RELEASE event
            KeyEvent event;
            event.key = keyCode;
            event.type = KEY_EVENT_RELEASE;
            event.row = row;
            event.col = col;
            event.timestamp = now;
            event.repeatCount = 0;
            addEvent(event);
            
            _totalKeyReleases++;
            
            KEYPAD_DEBUGF("Key 0x%02X: RELEASED", keyCode);
            
            // Check for double-click
            if (!state.wasDoubleClick && 
                state.releaseTime - state.pressTime < _doubleClickTime) {
                
                // Wait to see if key is pressed again
                state.state = KEY_STATE_WAIT_DOUBLE;
                state.wasDoubleClick = false;
            } else {
                // Return to idle
                state.state = KEY_STATE_IDLE;
                state.wasDoubleClick = false;
            }
            break;
        
        // ====================================================================
        // WAIT_DOUBLE STATE (waiting for second press)
        // ====================================================================
        case KEY_STATE_WAIT_DOUBLE:
            if (currentlyPressed && !previouslyPressed) {
                // Second press detected - double-click!
                state.state = KEY_STATE_PRESSED;
                state.pressTime = now;
                state.wasDoubleClick = true;
                
                // Generate DOUBLE_CLICK event
                KeyEvent dcEvent;
                dcEvent.key = keyCode;
                dcEvent.type = KEY_EVENT_DOUBLE_CLICK;
                dcEvent.row = row;
                dcEvent.col = col;
                dcEvent.timestamp = now;
                dcEvent.repeatCount = 0;
                addEvent(dcEvent);
                
                _totalDoubleClicks++;
                
                KEYPAD_DEBUGF("Key 0x%02X: DOUBLE-CLICK", keyCode);
            } else if (now - state.releaseTime >= _doubleClickTime) {
                // Double-click window expired
                state.state = KEY_STATE_IDLE;
                state.wasDoubleClick = false;
            }
            break;
    }
}

/**
 * @brief Add event to queue
 * 
 * @param event Event to add
 * @return true if added, false if queue is full
 */
bool Keypad::addEvent(const KeyEvent& event) {
    uint8_t nextHead = (_eventQueueHead + 1) % KEY_EVENT_QUEUE_SIZE;
    
    // Check if queue is full
    if (nextHead == _eventQueueTail) {
        KEYPAD_DEBUG("ERROR: Event queue full!");
        return false;
    }
    
    // Add event to queue
    _eventQueue[_eventQueueHead] = event;
    _eventQueueHead = nextHead;
    
    return true;
}

// ============================================================================
// STATISTICS
// ============================================================================

/**
 * @brief Update scan rate statistics
 */
void Keypad::updateScanRate() {
    unsigned long now = millis();
    unsigned long elapsed = now - _lastStatsTime;
    
    if (elapsed >= 1000) {  // Update every second
        _scanRate = (_scanCount * 1000.0f) / elapsed;
        _scanCount = 0;
        _lastStatsTime = now;
    }
}

/**
 * @brief Print keypad statistics
 */
void Keypad::printStats() const {
    #ifdef DEBUG
    DEBUG_SERIAL.println("\n===== KEYPAD STATISTICS =====");
    DEBUG_SERIAL.printf("Scan Rate: %.1f Hz\n", _scanRate);
    DEBUG_SERIAL.printf("Total Presses: %lu\n", _totalKeyPresses);
    DEBUG_SERIAL.printf("Total Releases: %lu\n", _totalKeyReleases);
    DEBUG_SERIAL.printf("Long Presses: %lu\n", _totalLongPresses);
    DEBUG_SERIAL.printf("Double-Clicks: %lu\n", _totalDoubleClicks);
    DEBUG_SERIAL.printf("Events in Queue: %d\n", getEventCount());
    DEBUG_SERIAL.printf("Currently Pressed: %d keys\n", isAnyKeyPressed() ? 1 : 0);
    DEBUG_SERIAL.println("============================\n");
    #endif
}

/**
 * @brief Print current key states (debug)
 */
void Keypad::printKeyStates() const {
    #ifdef DEBUG
    DEBUG_SERIAL.println("\n===== KEY STATES =====");
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        DEBUG_SERIAL.print("Row ");
        DEBUG_SERIAL.print(row);
        DEBUG_SERIAL.print(": ");
        
        for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
            uint8_t index = getKeyIndex(row, col);
            DEBUG_SERIAL.print(_currentKeyState[index] ? "[X] " : "[ ] ");
        }
        DEBUG_SERIAL.println();
    }
    DEBUG_SERIAL.println("======================\n");
    #endif
}

// ============================================================================
// T9 TEXT ENTRY
// ============================================================================

/**
 * @brief Get T9 character for key and tap count
 * 
 * @param key Key code (2-9)
 * @param tapCount Tap count (0-based)
 * @param uppercase true for uppercase
 * @return Character, or 0 if invalid
 */
char Keypad::getT9Char(uint8_t key, uint8_t tapCount, bool uppercase) {
    // Handle numeric keys 2-9
    if (key >= '2' && key <= '9') {
        uint8_t keyIndex = key - '0';
        const char* chars = T9_CHARS[keyIndex];
        uint8_t charCount = strlen(chars);
        
        if (tapCount < charCount) {
            char c = chars[tapCount];
            return uppercase ? toupper(c) : c;
        }
    }
    
    // Handle 0 key (space)
    if (key == '0') {
        return ' ';
    }
    
    // Handle * key (symbols)
    if (key == '*') {
        uint8_t symbolCount = sizeof(T9_SYMBOLS) - 1;
        if (tapCount < symbolCount) {
            return T9_SYMBOLS[tapCount];
        }
    }
    
    return 0;  // Invalid
}

/**
 * @brief Get number of T9 characters for a key
 * 
 * @param key Key code (2-9)
 * @return Character count
 */
uint8_t Keypad::getT9CharCount(uint8_t key) {
    if (key >= '2' && key <= '9') {
        uint8_t keyIndex = key - '0';
        return strlen(T9_CHARS[keyIndex]);
    }
    
    if (key == '0') {
        return 1;  // Space
    }
    
    if (key == '*') {
        return sizeof(T9_SYMBOLS) - 1;
    }
    
    return 0;
}

// ============================================================================
// FREERTOS TASK
// ============================================================================

/**
 * @brief Static task function for automatic scanning
 * 
 * @param parameter Pointer to Keypad instance
 */
void Keypad::scanTask(void* parameter) {
    Keypad* keypad = static_cast<Keypad*>(parameter);
    
    KEYPAD_DEBUG("Scan task started");
    
    while (keypad->_scanningEnabled) {
        keypad->scan();
        
        // Delay until next scan interval
        vTaskDelay(pdMS_TO_TICKS(keypad->_scanInterval));
    }
    
    KEYPAD_DEBUG("Scan task ended");
    vTaskDelete(nullptr);
}

// ============================================================================
// END OF FILE
// ============================================================================
