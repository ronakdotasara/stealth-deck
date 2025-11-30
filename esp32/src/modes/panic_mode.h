/**
 * ============================================================================
 * panic_mode.h - Panic Mode for Stealth Deck
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-30
 * Author: Stealth Deck Project
 * License: MIT
 * ============================================================================
 */

#ifndef PANIC_MODE_H
#define PANIC_MODE_H

#include <Arduino.h>
#include "../config.h"              // ✅ SystemMode, KeyEvent
#include "../input/keypad.h"        // ✅ KeyEvent type

// ============================================================================
// PANIC MODE CONSTANTS
// ============================================================================

#define PANIC_BLINK_INTERVAL  200
#define PANIC_TIMEOUT_MS     30000
#define PANIC_RECOVERY_KEY   KEY_HASH

enum PanicTrigger {
    PANIC_TRIGGER_NONE,
    PANIC_TRIGGER_KEY_COMBO,
    PANIC_TRIGGER_PI_SIGNAL,
    PANIC_TRIGGER_TIMEOUT,
    PANIC_TRIGGER_MANUAL
};

class PanicMode {
public:
    PanicMode();
    
    void begin();
    void reset();
    
    // ✅ ADDED: Main.cpp integration methods
    void activate() {
        activate(PANIC_TRIGGER_MANUAL);
    }
    
    void deactivate() {
        Serial.println("Panic mode deactivated");
    }
    
    void update();
    
    // ✅ ADDED: KeyEvent handling for main.cpp
    void handleKeyEvent(KeyEvent event) {
        if (event.type == KEY_EVENT_PRESS) {
            handleKey(event.key);
        }
    }
    
    // Core panic functions
    void activate(PanicTrigger trigger);
    bool isActive();
    PanicTrigger getTrigger();
    
    void displayPanicScreen();
    void displayRecoveryPrompt();
    
    void enableWireless(bool enable);
    void clearSensitiveData();
    void lockDevice();
    
    unsigned long getActivationTime();

private:
    bool active;
    PanicTrigger trigger;
    unsigned long activationTime;
    unsigned long lastBlinkTime;
    bool blinkState;
    
    void handleKey(uint8_t key);
    void sendPanicSignalToPI();
    void switchToCalculatorMode();
    void displayFakeHistory();
    void flashScreen();
    void playPanicSound();
};

#endif // PANIC_MODE_H
