/**
 * ============================================================================
 * @file config.h
 * @brief COMPLETE Configuration - Fixes ALL Compile Errors
 * @version 1.0.0
 * @date 2025-11-30
 * @author Stealth Deck Project
 * @license MIT
 * ============================================================================
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ============================================================================
// HARDWARE PINS (LILYGO T-Display-S3 AMOLED + 5x4 Keypad)
// ============================================================================

#define KEYPAD_ROWS 5
#define KEYPAD_COLS 4

#define KEYPAD_ROW_1  2
#define KEYPAD_ROW_2  3
#define KEYPAD_ROW_3  4
#define KEYPAD_ROW_4  5
#define KEYPAD_ROW_5  6

#define KEYPAD_COL_1  7
#define KEYPAD_COL_2  8
#define KEYPAD_COL_3  9
#define KEYPAD_COL_4 10

#define UART_RX_PIN  11
#define UART_TX_PIN  12

// ============================================================================
// DISPLAY CONFIGURATION (T-Display-S3 AMOLED)
// ============================================================================

#define DISPLAY_WIDTH   320
#define DISPLAY_HEIGHT  170
#define DISPLAY_ROTATION 1

#define BRIGHTNESS_STEALTH  30
#define BRIGHTNESS_NORMAL  128
#define BRIGHTNESS_OUTDOOR 255

// ✅ ADDED: DISPLAY POWER MODES (Fixes display_driver.cpp errors)
#define DISPLAY_POWER_NORMAL  0
#define DISPLAY_POWER_OFF     1
#define DISPLAY_POWER_SLEEP   2

// TFT_eSPI Colors
#define COLOR_BLACK   TFT_BLACK
#define COLOR_WHITE   TFT_WHITE
#define COLOR_RED     TFT_RED
#define COLOR_GREEN   TFT_GREEN
#define COLOR_BLUE    TFT_BLUE
#define COLOR_YELLOW  TFT_YELLOW
#define COLOR_CYAN    TFT_CYAN
#define COLOR_MAGENTA TFT_MAGENTA
#define COLOR_GRAY    TFT_DARKGREY

// ============================================================================
// KEYPAD CODES (COMPLETE 5x4 Matrix)
// ============================================================================

#define KEY_0    0
#define KEY_1    1
#define KEY_2    2
#define KEY_3    3
#define KEY_4    4
#define KEY_5    5
#define KEY_6    6
#define KEY_7    7
#define KEY_8    8
#define KEY_9    9
#define KEY_FN   10
#define KEY_FIX  11
#define KEY_STAR 12
#define KEY_HASH 13

// Additional keys for keypad.cpp
#define KEY_UP    14
#define KEY_DOWN  15
#define KEY_OK    16
#define KEY_BACK  17
#define KEY_PLUS  18
#define KEY_MINUS 19

// ============================================================================
// KEY STATES (Required by keypad.cpp)
// ============================================================================

#define KEY_STATE_IDLE          0
#define KEY_STATE_DEBOUNCING    1
#define KEY_STATE_PRESSED       2
#define KEY_STATE_RELEASED      3
#define KEY_STATE_HELD          4
#define KEY_STATE_LONG_PRESS    5
#define KEY_STATE_WAIT_DOUBLE   6
#define KEY_STATE_DOUBLE_PRESS  7

// ============================================================================
// UART PROTOCOL (ALL Missing Constants)
// ============================================================================

#define UART_BAUD_RATE        115200
#define UART_RX_BUFFER_SIZE   2048
#define UART_TX_BUFFER_SIZE   2048
#define UART_TIMEOUT_MS       1000
#define BT_BUFFER_SIZE        512

#define MSG_TYPE_DISPLAY_TEXT     0x01
#define MSG_TYPE_DISPLAY_IMAGE    0x02
#define MSG_TYPE_KEYPRESS         0x03
#define MSG_TYPE_CAMERA_CAPTURE   0x04
#define MSG_TYPE_MODE_CHANGE      0x05
#define MSG_TYPE_PANIC            0x06
#define MSG_TYPE_HEARTBEAT        0x07
#define MSG_TYPE_BATTERY_STATUS   0x08
#define MSG_TYPE_P2P_DATA         0x09
#define MSG_TYPE_ACK              0x0A
#define MSG_TYPE_NACK             0x0B

// ============================================================================
// ERROR CODES (Required by uart_protocol.cpp)
// ============================================================================

#define ERR_NONE          0
#define ERR_TIMEOUT       1
#define ERR_UART_TIMEOUT  2
#define ERR_CONN          3
#define ERR_INVALID_PARAM 4
#define ERR_NO_MEMORY     5
#define ERR_CRC_FAIL      6

// ============================================================================
// SECURITY
// ============================================================================

#define UNLOCK_SEQUENCE_LENGTH 6
#define UNLOCK_TIMEOUT_MS      3000
const uint8_t UNLOCK_SEQUENCE[UNLOCK_SEQUENCE_LENGTH] = {
    KEY_1, KEY_3, KEY_5, KEY_7, KEY_9, KEY_0
};

// ============================================================================
// TIMING
// ============================================================================

#define DEBOUNCE_DELAY_MS   50
#define LONG_PRESS_MS      1000
#define SYSTEM_LOOP_DELAY   10
#define HEARTBEAT_INTERVAL 5000

// ============================================================================
// UI CONFIGURATION (Required by ui_renderer.cpp)
// ============================================================================

#define MAX_WIDGETS        32
#define STATUS_BAR_HEIGHT  16
#define MENU_ITEM_HEIGHT   30

// ============================================================================
// SMART MODE CONSTANTS (Fixes smart_mode.cpp errors)
// ============================================================================

#define MAX_QUERY_LENGTH     128
#define MAX_RESPONSE_LENGTH  512  
#define MAX_HISTORY_ENTRIES   10

// ============================================================================
// MODES & EVENTS
// ============================================================================

enum SystemMode {
    MODE_CALCULATOR,
    MODE_SMART,
    MODE_PANIC
};

enum KeyEventType {
    KEY_EVENT_PRESS  = 0,
    KEY_EVENT_RELEASE = 1
};

// COMPLETE KeyEvent (Fixes keypad.cpp errors)
struct KeyEvent {
    uint8_t key;
    uint8_t type;
    uint8_t row;
    uint8_t col;
    unsigned long timestamp;
    uint8_t repeatCount;
};

// ============================================================================
// DEBUG
// ============================================================================

#ifdef DEBUG
    #define DEBUG_PRINT(x)      Serial.println(x)
    #define DEBUG_PRINTF(...)   Serial.printf(__VA_ARGS__)
#else
    #define DEBUG_PRINT(x)
    #define DEBUG_PRINTF(...)
#endif

// ============================================================================
// VERSION
// ============================================================================

#define FIRMWARE_VERSION "1.0.0"
#define BT_DEVICE_NAME   "StealthDeck"

#endif // CONFIG_H
