/**
 * ============================================================================
 * panic_mode.cpp - Panic Mode Implementation
 * ============================================================================
 */

#include "panic_mode.h"
#include "../communication/uart_protocol.h"
#include "../display/display_driver.h"
#include "../modes/calculator_mode.h"

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
        
        if (blinkState) {
            display.drawPixel(235, 5, true);
        } else {
            display.drawPixel(235, 5, false);
        }
        display.display();
    }
}

void PanicMode::displayPanicScreen() {
    display.clear();
    
    display.drawText(60, 250, "LOCKED", 3);
    
    display.drawRect(50, 240, 140, 40);
    
    display.display();
    
    delay(1000);
}

void PanicMode::displayRecoveryPrompt() {
    display.clear();
    
    display.drawText(10, 10, "Device Locked", 2);
    display.drawText(10, 40, "Enter unlock code:", 1);
    
    display.display();
}

void PanicMode::enableWireless(bool enable) {
    if (enable) {
        Serial.println("Enabling wireless...");
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
    Serial.println("Device locked");
}

unsigned long PanicMode::getActivationTime() {
    return activationTime;
}

void PanicMode::sendPanicSignalToPI() {
    Serial.println("Sending panic signal to Pi...");
    
    uart.sendPanicSignal();
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
    display.drawText(10, 10, "Calculator", 2);
    display.drawText(10, 40, "Recent:", 1);
    
    int y = 60;
    for (int i = 0; i < 5 && i < calculator.getHistoryCount(); i++) {
        auto* entry = calculator.getHistory(i);
        if (entry) {
            display.drawText(10, y, entry->expression, 1);
            y += 15;
        }
    }
    
    display.drawText(10, 520, "Normal calculator", 1);
    display.display();
}

void PanicMode::flashScreen() {
    for (int i = 0; i < 3; i++) {
        display.fill(true);
        display.display();
        delay(50);
        
        display.clear();
        display.display();
        delay(50);
    }
}

void PanicMode::playPanicSound() {
    // Optional: Add buzzer beep
}
