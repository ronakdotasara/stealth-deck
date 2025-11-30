/**
 * ============================================================================
 * panic_mode.cpp - Panic Mode Implementation
 * ============================================================================
 */

#include "panic_mode.h"
#include "../communication/uart_protocol.h"
#include "../display/display_driver.h"
#include "../modes/calculator_mode.h"
#include <WiFi.h>  // ADD THIS

extern UARTProtocol uart;
extern DisplayDriver display;
extern CalculatorMode calculator;

PanicMode::PanicMode() {
    active = false;
    trigger = PANIC_TRIGGER_NONE;
    activationTime = 0;
    lastBlinkTime = 0;
    blinkState = false;
}

void PanicMode::activate(PanicTrigger triggerType) {
    if (active) {
        return;
    }
    
    Serial.println("!!! PANIC MODE ACTIVATED !!!");
    
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

void PanicMode::deactivate() {
    if (!active) {
        return;
    }
    
    Serial.println("Panic mode deactivated");
    
    active = false;
    trigger = PANIC_TRIGGER_NONE;
}

bool PanicMode::isActive() {
    return active;
}

PanicTrigger PanicMode::getTrigger() {
    return trigger;
}

void PanicMode::update() {
    if (!active) {
        return;
    }
    
    if (millis() - lastBlinkTime > 500) {
        blinkState = !blinkState;
        lastBlinkTime = millis();
        
        // FIXED: Use COLOR_WHITE and COLOR_BLACK instead of true/false
        if (blinkState) {
            display.drawPixel(235, 5, COLOR_WHITE);
        } else {
            display.drawPixel(235, 5, COLOR_BLACK);
        }
        display.flush();  // FIXED: Use flush() instead of display()
    }
}

void PanicMode::displayPanicScreen() {
    display.clear();
    
    // FIXED: Add color parameter
    display.drawText(60, 250, "LOCKED", COLOR_WHITE, 3);
    
    // FIXED: Add color parameter
    display.drawRect(50, 240, 140, 40, COLOR_WHITE);
    
    display.flush();  // FIXED: Use flush() instead of display()
    
    delay(1000);
}

void PanicMode::displayRecoveryPrompt() {
    display.clear();
    
    // FIXED: Add color parameters
    display.drawText(10, 10, "Device Locked", COLOR_WHITE, 2);
    display.drawText(10, 40, "Enter unlock code:", COLOR_WHITE, 1);
    
    display.flush();  // FIXED: Use flush() instead of display()
}

void PanicMode::enableWireless(bool enable) {
    if (enable) {
        Serial.println("Enabling wireless...");
    } else {
        Serial.println("Disabling wireless...");
        
        WiFi.disconnect(true);
        WiFi.mode(WIFI_MODE_NULL);  // FIXED: Use WIFI_MODE_NULL instead of WIFI_OFF
        
        btStop();
    }
}

void PanicMode::clearSensitiveData() {
    Serial.println("Clearing sensitive data...");
}

void PanicMode::lockDevice() {
    Serial.println("Device locked");
}

unsigned long PanicMode::getActivationTime() {
    return activationTime;
}

void PanicMode::sendPanicSignalToPI() {
    Serial.println("Sending panic signal to Pi...");
    
    uart.sendPanic();  // FIXED: Use sendPanic() instead of sendPanicSignal()
}

void PanicMode::switchToCalculatorMode() {
    Serial.println("Switching to calculator mode...");
    
    calculator.reset();
    calculator.begin();
}

void PanicMode::displayFakeHistory() {
    Serial.println("Displaying fake calculator history...");
    
    calculator.generateFakeHistory();
    
    display.clear();
    
    // FIXED: Add color parameters
    display.drawText(10, 10, "Calculator", COLOR_WHITE, 2);
    display.drawText(10, 40, "Recent:", COLOR_WHITE, 1);
    
    int y = 60;
    for (int i = 0; i < 5 && i < calculator.getHistoryCount(); i++) {
        auto* entry = calculator.getHistory(i);
        if (entry) {
            // FIXED: Add color parameter
            display.drawText(10, y, entry->expression, COLOR_WHITE, 1);
            y += 15;
        }
    }
    
    // FIXED: Add color parameter
    display.drawText(10, 520, "Normal calculator", COLOR_WHITE, 1);
    display.flush();  // FIXED: Use flush() instead of display()
}

void PanicMode::flashScreen() {
    for (int i = 0; i < 3; i++) {
        // FIXED: Use fillRect to fill entire screen
        display.fillRect(0, 0, 240, 536, COLOR_WHITE);
        display.flush();  // FIXED: Use flush() instead of display()
        delay(50);
        
        display.clear();
        display.flush();  // FIXED: Use flush() instead of display()
        delay(50);
    }
}

void PanicMode::playPanicSound() {
    // Optional: Add buzzer beep
}
