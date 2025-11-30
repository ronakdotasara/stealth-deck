/**
 * ============================================================================
 * @file main.cpp
 * @brief Stealth Deck - Main Program Entry Point
 * @version 1.0.0
 * @date 2025-11-30
 * ============================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include "config.h"

// Display & UI
#include "display/display_driver.h"
#include "display/ui_renderer.h"

// Input
#include "input/keypad.h"
#include "input/t9_engine.h"

// Communication
#include "communication/uart_protocol.h"
// #include "communication/bluetooth_spp.h"   // Classic BT not supported on ESP32-S3
#include "communication/wifi_sniffer.h"

// Modes
#include "modes/calculator_mode.h"
#include "modes/smart_mode.h"
#include "modes/panic_mode.h"

// P2P & Security
#include "p2p/p2p_manager.h"
#include "p2p/encryption.h"

// Utilities
#include "utils/state_machine.h"

// ============================================================================
// GLOBAL OBJECTS
// ============================================================================

// Core Hardware
DisplayDriver display;
Keypad keypad;
UIRenderer uiRenderer(&display);

// Communication
UARTProtocol uart;
// BluetoothSPP bluetooth;               // Disabled for ESP32-S3
WiFiSniffer wifiSniffer;

// Modes
CalculatorMode calculator;
SmartMode smartMode;
PanicMode panicMode;

// P2P & Security
P2PManager p2pManager;
Encryption encryption;

// State Management
StateMachine stateMachine;
T9Engine t9Engine;

// ============================================================================
// SYSTEM STATE
// ============================================================================

enum SystemMode {
    MODE_CALCULATOR,
    MODE_SMART,
    MODE_P2P,
    MODE_WIFI_SNIFFER,
    MODE_SETTINGS,
    MODE_PANIC
};

SystemMode currentMode = MODE_CALCULATOR;
bool deviceUnlocked = false;
bool firstBoot = true;

// Unlock sequence tracking
uint8_t unlockSequence[UNLOCK_SEQUENCE_LENGTH];
uint8_t unlockIndex = 0;
unsigned long lastKeyPressTime = 0;

// Performance tracking
unsigned long lastUpdateTime = 0;
unsigned long frameCount = 0;
float currentFPS = 0.0f;

// ============================================================================
// FUNCTION PROTOTYPES
// ============================================================================

void initializeHardware();
void initializeCommunication();
void initializeModes();
void showBootScreen();
void showReadyScreen();
void handleKeyEvent(KeyEvent event);
void handleUnlockSequence(uint8_t key);
void switchMode(SystemMode newMode);
void updateCurrentMode();
void checkPanicTriggers();
void updateStatusBar();
void updatePerformanceStats();
void handleUARTMessages();
void printSystemInfo();

// ============================================================================
// SETUP
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n");
    Serial.println("╔════════════════════════════════════════════════════════╗");
    Serial.println("║           STEALTH DECK - INITIALIZING                 ║");
    Serial.println("║         Covert Cybersecurity Tool v1.0.0              ║");
    Serial.println("╚════════════════════════════════════════════════════════╝");
    Serial.println();

    Serial.println("┌─ HARDWARE INITIALIZATION ─────────────────────────────┐");
    initializeHardware();
    Serial.println("└────────────────────────────────────────────────────────┘\n");

    showBootScreen();

    Serial.println("┌─ COMMUNICATION INITIALIZATION ────────────────────────┐");
    initializeCommunication();
    Serial.println("└────────────────────────────────────────────────────────┘\n");

    Serial.println("┌─ MODE INITIALIZATION ──────────────────────────────────┐");
    initializeModes();
    Serial.println("└────────────────────────────────────────────────────────┘\n");

    Serial.println("┌─ SECURITY INITIALIZATION ──────────────────────────────┐");
    Serial.println("│ [1/2] Initializing encryption...");
    encryption.begin();
    Serial.println("│ ✓ Encryption ready");
    Serial.println("│ [2/2] Loading unlock sequence...");
    memcpy(unlockSequence, UNLOCK_SEQUENCE, UNLOCK_SEQUENCE_LENGTH);
    Serial.println("│ ✓ Unlock sequence loaded");
    Serial.println("└────────────────────────────────────────────────────────┘\n");

    Serial.println("┌─ FINAL SETUP ──────────────────────────────────────────┐");
    Serial.println("│ Starting in CALCULATOR mode (locked)");
    currentMode = MODE_CALCULATOR;
    calculator.activate();
    Serial.println("│ ✓ System ready");
    Serial.println("└────────────────────────────────────────────────────────┘\n");

    showReadyScreen();
    printSystemInfo();

    Serial.println("╔════════════════════════════════════════════════════════╗");
    Serial.println("║              SYSTEM INITIALIZATION COMPLETE            ║");
    Serial.println("║                    STATUS: READY                       ║");
    Serial.println("╚════════════════════════════════════════════════════════╝\n");

    lastUpdateTime = millis();
    firstBoot = false;
}

// ============================================================================
// LOOP
// ============================================================================

void loop() {
    unsigned long now = millis();

    keypad.scan();
    if (keypad.available()) {
        KeyEvent event = keypad.read();
        handleKeyEvent(event);
    }

    checkPanicTriggers();
    handleUARTMessages();
    updateCurrentMode();

    if (now - lastUpdateTime >= 1000) {
        updateStatusBar();
        updatePerformanceStats();
        lastUpdateTime = now;
    }

    delay(1);
    frameCount++;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void initializeHardware() {
    Serial.println("│ [1/2] Initializing display...");
    if (!display.begin()) {
        Serial.println("│ ✗ ERROR: Display initialization failed!");
        while (1) delay(1000);
    }
    Serial.println("│ ✓ Display ready (240×536 OLED)");

    Serial.println("│ [2/2] Initializing keypad...");
    if (!keypad.begin()) {
        Serial.println("│ ✗ ERROR: Keypad initialization failed!");
        while (1) delay(1000);
    }
    Serial.println("│ ✓ Keypad ready (5×4 matrix)");
}

void initializeCommunication() {
    Serial.println("│ [1/3] Initializing UART...");
    if (!uart.begin(UART_RX_PIN, UART_TX_PIN, 115200)) {
        Serial.println("│ ⚠ WARNING: UART initialization failed");
    } else {
        Serial.println("│ ✓ UART ready (115200 baud)");
    }

    Serial.println("│ [2/3] Bluetooth...");
    Serial.println("│ ⚠ Bluetooth disabled (ESP32-S3 has no Classic SPP)");

    Serial.println("│ [3/3] Initializing WiFi...");
    wifiSniffer.begin();
    Serial.println("│ ✓ WiFi ready");
}

void initializeModes() {
    Serial.println("│ [1/3] Initializing calculator mode...");
    calculator.begin();
    Serial.println("│ ✓ Calculator mode ready");

    Serial.println("│ [2/3] Initializing smart mode...");
    smartMode.begin();
    Serial.println("│ ✓ Smart mode ready");

    Serial.println("│ [3/3] Initializing panic mode...");
    Serial.println("│ ✓ Panic mode ready");
}

// ============================================================================
// DISPLAY
// ============================================================================

void showBootScreen() {
    display.clear();
    display.drawText(40, 200, "STEALTH", COLOR_WHITE, 3);
    display.drawText(70, 240, "DECK", COLOR_WHITE, 3);
    display.drawText(80, 290, "v1.0.0", COLOR_WHITE, 1);
    display.drawRect(40, 320, 160, 10, COLOR_WHITE);

    for (int i = 0; i <= 158; i += 10) {
        display.fillRect(41, 321, i, 8, COLOR_WHITE);
        display.flush();
        delay(50);
    }
    delay(500);
}

void showReadyScreen() {
    display.clear();
    display.drawText(80, 250, "READY", COLOR_WHITE, 3);
    display.drawText(50, 290, "Calculator Mode", COLOR_WHITE, 1);
    display.flush();
    delay(1000);
}

void updateStatusBar() {
    // Status bar rendering handled by active mode if needed
}

// ============================================================================
// INPUT / MODES
// ============================================================================

void handleKeyEvent(KeyEvent event) {
    #ifdef DEBUG
    Serial.printf("Key Event: 0x%02X, Type: %d\n", event.key, event.type);
    #endif

    if (currentMode == MODE_CALCULATOR && !deviceUnlocked) {
        if (event.type == KEY_EVENT_PRESS) {
            handleUnlockSequence(event.key);
        }
    }

    switch (currentMode) {
        case MODE_CALCULATOR:   calculator.handleKeyEvent(event); break;
        case MODE_SMART:        smartMode.handleKeyEvent(event);  break;
        case MODE_P2P:          break;
        case MODE_WIFI_SNIFFER: break;
        case MODE_PANIC:        break;
        default:                break;
    }
}

void handleUnlockSequence(uint8_t key) {
    unsigned long now = millis();

    if (now - lastKeyPressTime > UNLOCK_TIMEOUT_MS) {
        unlockIndex = 0;
    }
    lastKeyPressTime = now;

    if (key == unlockSequence[unlockIndex]) {
        unlockIndex++;
        if (unlockIndex >= UNLOCK_SEQUENCE_LENGTH) {
            Serial.println("\n✓ DEVICE UNLOCKED!");
            deviceUnlocked = true;
            unlockIndex = 0;

            display.clear();
            display.drawText(60, 250, "UNLOCKED", COLOR_WHITE, 2);
            display.flush();
            delay(1000);

            switchMode(MODE_SMART);
        }
    } else {
        unlockIndex = 0;
    }
}

void switchMode(SystemMode newMode) {
    Serial.printf("Switching mode: %d -> %d\n", currentMode, newMode);

    switch (currentMode) {
        case MODE_CALCULATOR: calculator.deactivate(); break;
        case MODE_SMART:      smartMode.deactivate();  break;
        default: break;
    }

    currentMode = newMode;

    switch (newMode) {
        case MODE_CALCULATOR: calculator.activate();                    break;
        case MODE_SMART:      smartMode.activate();                     break;
        case MODE_PANIC:      panicMode.activate(PANIC_TRIGGER_MANUAL); break;
        default: break;
    }
}

void updateCurrentMode() {
    if (panicMode.isActive()) {
        panicMode.update();
        return;
    }

    switch (currentMode) {
        case MODE_CALCULATOR: calculator.update();  break;
        case MODE_SMART:      smartMode.update();   break;
        case MODE_P2P:        p2pManager.update();  break;
        default:              break;
    }
}

// ============================================================================
// PANIC
// ============================================================================

void checkPanicTriggers() {
    if (keypad.isComboPressed(KEY_FN, KEY_FIX)) {
        if (!panicMode.isActive()) {
            Serial.println("\n!!! PANIC MODE TRIGGERED !!!");
            switchMode(MODE_PANIC);
        }
    }
}

// ============================================================================
// COMMUNICATION
// ============================================================================

void handleUARTMessages() {
    uart.process();

    if (uart.available()) {
        UARTMessage msg = uart.read();

        switch (msg.type) {
            case MSG_TYPE_DISPLAY_TEXT:
                break;
            case MSG_TYPE_MODE_CHANGE:
                break;
            case MSG_TYPE_PANIC:
                switchMode(MODE_PANIC);
                break;
            default:
                break;
        }
    }
}

// ============================================================================
// PERFORMANCE & INFO
// ============================================================================

void updatePerformanceStats() {
    currentFPS = frameCount;
    frameCount = 0;

    #ifdef DEBUG
    Serial.printf("FPS: %.1f | Free Heap: %d bytes\n",
                  currentFPS, ESP.getFreeHeap());
    #endif
}

void printSystemInfo() {
    Serial.println("\n╔════════════════════════════════════════════════════════╗");
    Serial.println("║                   SYSTEM INFORMATION                   ║");
    Serial.println("╠════════════════════════════════════════════════════════╣");
    Serial.printf("║ Chip Model:      ESP32-S3                              ║\n");
    Serial.printf("║ CPU Frequency:   %d MHz                             ║\n", ESP.getCpuFreqMHz());
    Serial.printf("║ Flash Size:      %d MB                               ║\n", ESP.getFlashChipSize() / (1024 * 1024));
    Serial.printf("║ Free Heap:       %d bytes                          ║\n", ESP.getFreeHeap());
    Serial.printf("║ PSRAM:           %d bytes                          ║\n", ESP.getPsramSize());
    Serial.println("╠════════════════════════════════════════════════════════╣");
    Serial.println("║ Display:         240×536 OLED AMOLED                   ║");
    Serial.println("║ Keypad:          5×4 Matrix                            ║");
    Serial.println("║ Communication:   UART, WiFi                            ║");
    Serial.println("╚════════════════════════════════════════════════════════╝\n");
}
