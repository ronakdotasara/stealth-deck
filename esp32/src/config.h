/**
 * ============================================================================
 * @file config.h
 * @brief Configuration and Definitions for Stealth Deck
 * @version 1.0.0
 * @date 2025-11-30
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Central configuration file containing all hardware pin definitions,
 * constants, message types, and system parameters for the ESP32 firmware.
 * 
 * ============================================================================
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>
#include <lvgl.h>

// ============================================================================
// Hardware Pin Definitions
// ============================================================================

// Keypad Dimensions
#define KEYPAD_ROWS 5
#define KEYPAD_COLS 4

// Keypad Row Pins (Output - Active LOW)
#define KEYPAD_ROW_1 15
#define KEYPAD_ROW_2 16
#define KEYPAD_ROW_3 17
#define KEYPAD_ROW_4 18
#define KEYPAD_ROW_5 19

// Keypad Column Pins (Input - PULLUP)
#define KEYPAD_COL_1 21
#define KEYPAD_COL_2 22
#define KEYPAD_COL_3 23
#define KEYPAD_COL_4 25

// UART Pins (Communication with Raspberry Pi)
#define UART_RX_PIN  16
#define UART_TX_PIN  17

// ============================================================================
// Key Code Definitions
// ============================================================================

#define KEY_NONE     0
#define KEY_1        1
#define KEY_2        2
#define KEY_3        3
#define KEY_4        4
#define KEY_5        5
#define KEY_6        6
#define KEY_7        7
#define KEY_8        8
#define KEY_9        9
#define KEY_0        10
#define KEY_STAR     11
#define KEY_HASH     12
#define KEY_UP       13
#define KEY_DOWN     14
#define KEY_OK       15
#define KEY_BACK     16
#define KEY_FN       17
#define KEY_PLUS     18
#define KEY_MINUS    19
#define KEY_FIX      20

// ============================================================================
// Key State Definitions
// ============================================================================

#define KEY_STATE_IDLE           0
#define KEY_STATE_DEBOUNCING     1
#define KEY_STATE_PRESSED        2
#define KEY_STATE_RELEASED       3
#define KEY_STATE_HELD           4
#define KEY_STATE_LONG_PRESS     5
#define KEY_STATE_WAIT_DOUBLE    6
#define KEY_STATE_DOUBLE_PRESS   7

// ============================================================================
// UART Protocol Message Types
// ============================================================================

#define MSG_TYPE_DISPLAY_TEXT      0x01
#define MSG_TYPE_DISPLAY_IMAGE     0x02
#define MSG_TYPE_KEYPRESS          0x03
#define MSG_TYPE_CAMERA_CAPTURE    0x04
#define MSG_TYPE_MODE_CHANGE       0x05
#define MSG_TYPE_PANIC             0x06
#define MSG_TYPE_HEARTBEAT         0x07
#define MSG_TYPE_BATTERY_STATUS    0x08
#define MSG_TYPE_P2P_DATA          0x09
#define MSG_TYPE_ACK               0x0A
#define MSG_TYPE_NACK              0x0B

// ============================================================================
// Error Codes
// ============================================================================

#define ERR_NONE              0
#define ERR_OK                0
#define ERR_TIMEOUT           1
#define ERR_UART_TIMEOUT      2
#define ERR_CONN              3
#define ERR_INVALID_PARAM     4
#define ERR_NO_MEMORY         5
#define ERR_CRC_FAIL          6

// ============================================================================
// UART Configuration
// ============================================================================

#define UART_BAUD_RATE        115200
#define UART_RX_BUFFER_SIZE   2048
#define UART_TX_BUFFER_SIZE   2048
#define UART_TIMEOUT_MS       1000

// ============================================================================
// Bluetooth Configuration
// ============================================================================

#define BT_DEVICE_NAME        "StealthDeck-ESP32"
#define BT_BUFFER_SIZE        512

// ============================================================================
// Display Configuration
// ============================================================================

#define DISPLAY_WIDTH         240
#define DISPLAY_HEIGHT        536
#define DISPLAY_ROTATION      0

// Display Colors (LVGL)
#define COLOR_BLACK           lv_color_hex(0x000000)
#define COLOR_WHITE           lv_color_hex(0xFFFFFF)
#define COLOR_RED             lv_color_hex(0xFF0000)
#define COLOR_GREEN           lv_color_hex(0x00FF00)
#define COLOR_BLUE            lv_color_hex(0x0000FF)
#define COLOR_YELLOW          lv_color_hex(0xFFFF00)
#define COLOR_CYAN            lv_color_hex(0x00FFFF)
#define COLOR_MAGENTA         lv_color_hex(0xFF00FF)
#define COLOR_GRAY            lv_color_hex(0x808080)

// ============================================================================
// Timing Constants
// ============================================================================

#define DEBOUNCE_DELAY        50    // milliseconds
#define LONG_PRESS_DURATION   1000  // milliseconds
#define DOUBLE_PRESS_WINDOW   300   // milliseconds
#define HEARTBEAT_INTERVAL    5000  // milliseconds

// ============================================================================
// Buffer Sizes
// ============================================================================

#define MAX_MESSAGE_SIZE      1024
#define MAX_PAYLOAD_SIZE      512
#define MAX_FILENAME_LENGTH   64
#define MAX_RESPONSE_LENGTH   256

// ============================================================================
// P2P Transfer Configuration
// ============================================================================

#define P2P_CHUNK_SIZE        256
#define P2P_MAX_RETRIES       3
#define P2P_ACK_TIMEOUT       2000  // milliseconds

// ============================================================================
// System Configuration
// ============================================================================

#define SYSTEM_LOOP_DELAY     10    // milliseconds
#define WATCHDOG_TIMEOUT      30000 // milliseconds

// ============================================================================
// Security Configuration
// ============================================================================

#define UNLOCK_SEQUENCE_LENGTH 5
#define UNLOCK_TIMEOUT_MS      5000  // Time window to complete unlock sequence

// Default unlock sequence: FN, 5, 7, 3, 9
const uint8_t UNLOCK_SEQUENCE[UNLOCK_SEQUENCE_LENGTH] = {
    KEY_FN, KEY_5, KEY_7, KEY_3, KEY_9
};

// ============================================================================
// Calculator Configuration
// ============================================================================

#define MAX_HISTORY_ENTRIES   20
#define MAX_EXPRESSION_LENGTH 64
#define MAX_RESULT_LENGTH     32

// ============================================================================
// WiFi Sniffer Configuration
// ============================================================================

#define MAX_WIFI_NETWORKS     50
#define WIFI_SCAN_TIMEOUT     10000  // milliseconds

// ============================================================================
// Debug Configuration
// ============================================================================

#ifdef DEBUG
  #define DEBUG_SERIAL        Serial
  #define DEBUG_PRINT(x)      Serial.println(x)
  #define DEBUG_PRINTF(...)   Serial.printf(__VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTF(...)
#endif

// ============================================================================
// Panic Mode Configuration
// ============================================================================

#define PANIC_FLASH_COUNT     3
#define PANIC_FLASH_DELAY     50  // milliseconds

// ============================================================================
// UI Configuration
// ============================================================================

#define MAX_WIDGETS           32
#define STATUS_BAR_HEIGHT     16
#define MENU_ITEM_HEIGHT      30

// ============================================================================
// Helper Macros
// ============================================================================

#define MIN(a, b)             ((a) < (b) ? (a) : (b))
#define MAX(a, b)             ((a) > (b) ? (a) : (b))
#define CONSTRAIN(x, a, b)    ((x) < (a) ? (a) : ((x) > (b) ? (b) : (x)))

// ============================================================================
// Version Information
// ============================================================================

#define FIRMWARE_VERSION      "1.0.0"
#define FIRMWARE_BUILD_DATE   __DATE__
#define FIRMWARE_BUILD_TIME   __TIME__

#endif // CONFIG_H
