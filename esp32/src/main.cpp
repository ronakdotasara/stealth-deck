/**
 * @file main.cpp - FIXED: No Duplicate DisplayDriver
 * @version 1.0.2 | LINKER ERROR FIXED
 */

#include <Arduino.h>
#include <WiFi.h>
#include "config.h"

// Display (extern from display_driver.h)
#include "display/display_driver.h"  

// Input
#include "input/keypad.h"

// Modes
#include "modes/calculator_mode.h"
#include "modes/smart_mode.h"
#include "modes/panic_mode.h"

// Communication
#include "communication/uart_protocol.h"
#include "communication/wifi_sniffer.h"

// ============================================================================
// FUNCTION PROTOTYPES
// ============================================================================
void showBootScreen();
void showReadyScreen();
void handleKeyEvent(KeyEvent event);
void handleUnlockSequence(uint8_t key);
void switchToSmartMode();
void switchToPanicMode();

// ============================================================================
// GLOBAL OBJECTS (✅ FIXED: NO DisplayDriver display here!)
// ============================================================================
Keypad keypad;
UARTProtocol uart;
WiFiSniffer wifiSniffer;
CalculatorMode calculator;
SmartMode smartMode;
PanicMode panicMode;

// ✅ display is extern from display_driver.cpp - NO LOCAL DEFINITION!

// ============================================================================
// SYSTEM STATE
// ============================================================================
SystemMode currentMode = MODE_CALCULATOR;
bool deviceUnlocked = false;
uint8_t unlockIndex = 0;
unsigned long lastKeyPressTime = 0;

// ============================================================================
// SETUP
// ============================================================================
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n╔════════════════════════════════════════════════════════╗");
    Serial.println("║           STEALTH DECK v1.0.2 - INITIALIZING          ║");
    Serial.println("╚════════════════════════════════════════════════════════╝");
    
    // 1. Initialize Display (uses global display)
    Serial.println("┌─ DISPLAY ───────────────────────────────────────────────┐");
    if (!display.begin()) {  // ✅ Global display from display_driver.cpp
        Serial.println("│ ✗ ERROR: Display failed!");
        while(1) { delay(1000); }
    }
    Serial.println("│ ✓ LILYGO T-Display-S3 AMOLED ready");
    Serial.println("└────────────────────────────────────────────────────────┘\n");
    
    showBootScreen();
    
    // 2. Initialize Keypad
    Serial.println("┌─ INPUT ─────────────────────────────────────────────────┐");
    if (!keypad.begin()) {
        Serial.println("│ ✗ ERROR: Keypad failed!");
        while(1) { delay(1000); }
    }
    Serial.println("│ ✓ 5×4 Matrix keypad ready");
    Serial.println("└────────────────────────────────────────────────────────┘\n");
    
    // 3. Initialize Communication
    Serial.println("┌─ COMMUNICATION ────────────────────────────────────────┐");
    uart.begin(UART_RX_PIN, UART_TX_PIN, UART_BAUD_RATE);
    Serial.println("│ ✓ UART ready");
    
    wifiSniffer.begin();
    Serial.println("│ ✓ WiFi sniffer ready");
    Serial.println("└────────────────────────────────────────────────────────┘\n");
    
    // 4. Initialize Modes
    Serial.println("┌─ MODES ─────────────────────────────────────────────────┐");
    calculator.begin();
    smartMode.begin();
    panicMode.begin();
    Serial.println("│ ✓ All modes ready");
    Serial.println("└────────────────────────────────────────────────────────┘\n");
    
    // Start in locked calculator mode
    currentMode = MODE_CALCULATOR;
    calculator.activate();
    showReadyScreen();
    
    Serial.println("✓ SYSTEM READY - Press 1-3-5-7-9-0 to unlock");
    Serial.println("╚════════════════════════════════════════════════════════╝\n");
}

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
    keypad.scan();
    if (keypad.available()) {
        KeyEvent event = keypad.read();
        handleKeyEvent(event);
    }
    
    switch (currentMode) {
        case MODE_CALCULATOR: calculator.update(); break;
        case MODE_SMART:     smartMode.update();   break;
        case MODE_PANIC:     panicMode.update();   break;
    }
    
    uart.process();
    delay(SYSTEM_LOOP_DELAY);
}

// ============================================================================
// BOOT SCREENS (UNCHANGED)
// ============================================================================
void showBootScreen() {
    display.clear(COLOR_BLACK);
    display.drawText(50, 30, "STEALTH", COLOR_WHITE, 3);
    display.drawText(90, 80, "DECK", COLOR_WHITE, 3);
    display.drawText(130, 130, FIRMWARE_VERSION, COLOR_WHITE, 2);
    
    display.drawRect(40, 150, 240, 8, COLOR_WHITE);
    for (int i = 0; i <= 238; i += 20) {
        display.fillRect(41, 151, i, 6, COLOR_GREEN);
        display.flush();
        delay(40);
    }
    delay(500);
}

void showReadyScreen() {
    display.clear(COLOR_BLACK);
    display.drawText(80, 40, "READY", COLOR_WHITE, 3);
    display.drawText(30, 90, "Calculator Mode", COLOR_WHITE, 2);
    display.drawText(60, 130, "(Locked)", COLOR_GRAY, 1);
    display.drawText(70, 150, "1-3-5-7-9-0", COLOR_WHITE, 2);
    display.flush();
}

// ============================================================================
// INPUT HANDLING (UNCHANGED)
// ============================================================================
void handleKeyEvent(KeyEvent event) {
    Serial.printf("Key: %d, Type: %d\n", event.key, event.type);
    
    if (currentMode == MODE_CALCULATOR && !deviceUnlocked && event.type == KEY_EVENT_PRESS) {
        handleUnlockSequence(event.key);
        return;
    }
    
    switch (currentMode) {
        case MODE_CALCULATOR: calculator.handleKeyEvent(event); break;
        case MODE_SMART:     smartMode.handleKeyEvent(event);   break;
        case MODE_PANIC:     panicMode.handleKeyEvent(event);   break;
    }
}

void handleUnlockSequence(uint8_t key) {
    unsigned long now = millis();
    
    if (now - lastKeyPressTime > UNLOCK_TIMEOUT_MS) {
        unlockIndex = 0;
    }
    lastKeyPressTime = now;
    
    if (key == UNLOCK_SEQUENCE[unlockIndex]) {
        unlockIndex++;
        
        if (unlockIndex >= UNLOCK_SEQUENCE_LENGTH) {
            Serial.println("\n🎉 DEVICE UNLOCKED!");
            deviceUnlocked = true;
            unlockIndex = 0;
            
            display.clear(COLOR_BLACK);
            display.drawText(40, 60, "UNLOCKED", COLOR_GREEN, 3);
            display.drawText(60, 120, "Full access", COLOR_WHITE, 2);
            display.flush();
            delay(1500);
            
            showReadyScreen();
        }
    } else {
        unlockIndex = 0;
        Serial.printf("Unlock fail: expected %d, got %d\n", UNLOCK_SEQUENCE[unlockIndex], key);
    }
}

void switchToSmartMode() {
    currentMode = MODE_SMART;
    smartMode.activate();
    Serial.println("Switched to Smart Mode");
}

void switchToPanicMode() {
    currentMode = MODE_PANIC;
    panicMode.activate();
    Serial.println("PANIC MODE ACTIVATED");
}
