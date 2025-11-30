/**
 * ============================================================================
 * panic_mode.cpp - Panic Mode Implementation
 * ============================================================================
 */

#include "panic_mode.h"
#include "../communication/uart_protocol.h"
#include "../display/display_driver.h"
#include "../modes/calculator_mode.h"
#include <WiFi.h>
#include <BluetoothSerial.h>

extern UARTProtocol uart;
extern DisplayDriver display;
extern CalculatorMode calculator;

// ============================================================================
// CONSTRUCTOR + MAIN INTEGRATION
// ============================================================================

PanicMode::PanicMode() {
    reset();
}

void PanicMode::begin() {
    Serial.println("│ ✓ Panic mode ready");
}

void PanicMode::reset() {
    active = false;
    trigger = PANIC_TRIGGER_NONE;
    activationTime = 0;
    lastBlinkTime = 0;
    blinkState = false;
}

void PanicMode::handleKey(uint8_t key) {
    if (!active) return;
    
    // Recovery key (HASH/#)
    if (key == PANIC_RECOVERY_KEY) {
        deactivate();
    }
}

// ============================================================================
// PANIC ACTIVATION
// ============================================================================

void PanicMode::activate(PanicTrigger triggerType) {
    if (active) return;
    
    Serial.println("🔴 !!! PANIC MODE ACTIVATED !!! 🔴");
    
    active = true;
    trigger = triggerType;
    activationTime = millis();
    
    flashScreen();
    sendPanicSignalToPI();
    enableWireless(false);
    switchToCalculatorMode();
    displayFakeHistory();
    lockDevice();
}

// ✅ REMOVED: Duplicate deactivate() - Uses header inline version

bool PanicMode::isActive() { return active; }
PanicTrigger PanicMode::getTrigger() { return trigger; }

// ============================================================================
// MAIN UPDATE LOOP
// ============================================================================

void PanicMode::update() {
    if (!active) return;
    
    unsigned long now = millis();
    
    // Timeout after 30 seconds
    if (now - activationTime > PANIC_TIMEOUT_MS) {
        deactivate();
        return;
    }
    
    // Blink indicator (top-right corner)
    if (now - lastBlinkTime > PANIC_BLINK_INTERVAL) {
        blinkState = !blinkState;
        lastBlinkTime = now;
        
        uint16_t dotColor = blinkState ? COLOR_RED : COLOR_BLACK;
        display.fillRect(300, 5, 15, 10, dotColor);
        display.flush();
    }
}

// ============================================================================
// DISPLAY SCREENS (320x170)
// ============================================================================

void PanicMode::displayPanicScreen() {
    display.clear(COLOR_BLACK);
    display.drawText(80, 50, "LOCKED", COLOR_RED, 3);
    display.drawRect(70, 40, 180, 50, COLOR_WHITE);
    display.flush();
    delay(1000);
}

void PanicMode::displayRecoveryPrompt() {
    display.clear(COLOR_BLACK);
    display.drawText(50, 20, "DEVICE LOCKED", COLOR_WHITE, 2);
    display.drawText(40, 60, "Press # to recover", COLOR_YELLOW, 1);
    display.flush();
}

// ============================================================================
// SECURITY FUNCTIONS
// ============================================================================

void PanicMode::enableWireless(bool enable) {
    if (enable) {
        Serial.println("Enabling wireless...");
        WiFi.mode(WIFI_STA);
    } else {
        Serial.println("Disabling wireless...");
        WiFi.disconnect(true);
        WiFi.mode(WIFI_OFF);
        btStop();
    }
}

void PanicMode::clearSensitiveData() {
    Serial.println("Clearing sensitive data...");
}

void PanicMode::lockDevice() {
    Serial.println("Device locked - Safe mode active");
}

unsigned long PanicMode::getActivationTime() { return activationTime; }

// ============================================================================
// COMMUNICATION
// ============================================================================

void PanicMode::sendPanicSignalToPI() {
    Serial.println("📡 Sending PANIC signal to Pi...");
    uart.sendPanic();
}

// ============================================================================
// CALCULATOR INTEGRATION
// ============================================================================

void PanicMode::switchToCalculatorMode() {
    Serial.println("Switching to safe calculator mode...");
    calculator.reset();
    calculator.generateFakeHistory();
}

void PanicMode::displayFakeHistory() {
    Serial.println("Displaying fake calculator history...");
    
    display.clear(COLOR_BLACK);
    display.drawText(80, 10, "CALCULATOR", COLOR_WHITE, 2);
    display.drawText(10, 35, "Recent History:", COLOR_GRAY, 1);
    
    int y = 55;
    for (int i = 0; i < 4 && i < calculator.getHistoryCount(); i++) {
        auto* entry = calculator.getHistory(i);
        if (entry) {
            char line[32];
            snprintf(line, 32, "%s=%.1f", entry->expression, entry->result);
            display.drawText(10, y, line, COLOR_WHITE, 1);
            y += 15;
        }
    }
    
    display.drawText(10, 150, "#: Recover", COLOR_YELLOW, 1);
    display.flush();
}

// ============================================================================
// VISUAL EFFECTS
// ============================================================================

void PanicMode::flashScreen() {
    for (int i = 0; i < 4; i++) {
        display.fillScreen(COLOR_RED);
        display.flush();
        delay(80);
        
        display.clear(COLOR_BLACK);
        display.flush();
        delay(80);
    }
}

void PanicMode::playPanicSound() {
    // TODO: Buzzer if available
}
