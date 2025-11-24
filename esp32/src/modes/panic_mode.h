/**
 * ============================================================================
 * panic_mode.h - Panic Mode for Stealth Deck
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-24
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Emergency panic mode implementation for instant lockdown.
 * Activates when FN+FIX keys are pressed simultaneously.
 * 
 * Features:
 * - Instant screen lock
 * - Return to calculator mode
 * - Display fake history
 * - Disable wireless
 * - Send panic signal to Pi
 * - Visual indicator
 * 
 * ============================================================================
 */

#ifndef PANIC_MODE_H
#define PANIC_MODE_H

#include <Arduino.h>

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
    
    void activate(PanicTrigger trigger);
    void deactivate();
    
    bool isActive();
    PanicTrigger getTrigger();
    
    void update();
    
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
    
    void sendPanicSignalToPI();
    void switchToCalculatorMode();
    void displayFakeHistory();
    
    void flashScreen();
    void playPanicSound();
};

#endif
