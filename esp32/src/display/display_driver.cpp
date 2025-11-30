/**
 * @file display_driver.cpp - LILYGO T-Display-S3 RM67162 Implementation
 * @version 1.1.0 | LILYGO OFFICIAL LIBRARY (FIXES BLACK SCREEN)
 * @date 2025-12-01 | SKU: 1729838
 */

#include "display_driver.h"

// Debug macros
#ifdef DEBUG
  #define DISPLAY_DEBUG(x) do { Serial.print("[DISPLAY] "); Serial.println(x); } while(0)
#else
  #define DISPLAY_DEBUG(x)
#endif

// ============================================================================
// SINGLE GLOBAL DEFINITION
// ============================================================================
DisplayDriver display;

// ============================================================================
// CONSTRUCTOR/DESTRUCTOR
// ============================================================================
DisplayDriver::DisplayDriver() {
    DISPLAY_DEBUG("DisplayDriver created");
}

DisplayDriver::~DisplayDriver() {
    displayOff();
    DISPLAY_DEBUG("DisplayDriver destroyed");
}

// ============================================================================
// INITIALIZATION - LILYGO OFFICIAL
// ============================================================================
bool DisplayDriver::begin() {
    DISPLAY_DEBUG("Initializing LILYGO T-Display-S3 RM67162...");
    
    // ✅ LILYGO Official init (NOT TFT_eSPI!)
    if (!_tft.begin()) {
        Serial.println("[DISPLAY] ✗ LILYGO init FAILED!");
        return false;
    }
    
    _tft.setRotation(_rotation);  // Landscape: 320x170
    
    // Backlight
    initBacklight();
    setBrightness(_brightness);
    
    // Clear & Test pattern
    fillScreen(COLOR_BLACK);
    fillScreen(COLOR_GREEN);
    delay(500);
    fillScreen(COLOR_BLACK);
    
    _initialized = true;
    DISPLAY_DEBUG("✓ LILYGO Display ready!");
    printInfo();
    return true;
}

void DisplayDriver::initBacklight() {
    pinMode(45, OUTPUT);
    digitalWrite(45, HIGH);  // ON by default
}

// ============================================================================
// DISPLAY CONTROL
// ============================================================================
void DisplayDriver::clear(uint16_t color) {
    if (!_initialized) return;
    fillScreen(color);
}

void DisplayDriver::fillScreen(uint16_t color) {
    if (!_initialized) return;
    _tft.fillScreen(color);
}

void DisplayDriver::displayOn() {
    if (!_initialized) return;
    digitalWrite(45, HIGH);
    setBrightness(_brightness);
    _sleeping = false;
}

void DisplayDriver::displayOff() {
    if (!_initialized) return;
    digitalWrite(45, LOW);
    _sleeping = true;
}

void DisplayDriver::setRotation(uint8_t rotation) {
    if (!_initialized) return;
    _rotation = rotation % 4;
    _tft.setRotation(_rotation);
}

// ============================================================================
// BRIGHTNESS CONTROL
// ============================================================================
void DisplayDriver::setBrightness(uint8_t brightness) {
    if (!_initialized) return;
    _brightness = constrain(brightness, 0, 255);
    analogWrite(45, _brightness);
}

void DisplayDriver::cycleBrightness() {
    if (_brightness <= 64)   setBrightness(128);
    else if (_brightness <= 128) setBrightness(255);
    else setBrightness(32);  // Stealth mode
}

void DisplayDriver::fadeToBlack(uint16_t duration_ms) {
    if (!_initialized) return;
    uint16_t steps = _brightness / 8;
    if (steps == 0) return;
    
    uint16_t step_ms = duration_ms / steps;
    for (uint16_t i = 0; i <= steps; i++) {
        uint8_t b = _brightness * (1.0 - (float)i / steps);
        analogWrite(45, b);
        delay(step_ms);
    }
}

// ============================================================================
// DRAWING PRIMITIVES (LILYGO SUPPORTED)
// ============================================================================
void DisplayDriver::drawPixel(int16_t x, int16_t y, uint16_t color) {
    if (!_initialized) return;
    _tft.drawPixel(x, y, color);
}

void DisplayDriver::drawRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color) {
    if (!_initialized) return;
    _tft.drawRect(x, y, w, h, color);
}

void DisplayDriver::fillRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color) {
    if (!_initialized) return;
    _tft.fillRect(x, y, w, h, color);
}

// ============================================================================
// TEXT RENDERING (LILYGO)
// ============================================================================
void DisplayDriver::drawText(int x, int y, const char* text, uint16_t color, uint8_t size) {
    if (!_initialized) return;
    _tft.setTextColor(color);
    _tft.setTextSize(size);
    _tft.setCursor(x, y);
    _tft.print(text);
}

void DisplayDriver::drawNumber(int x, int y, long num, uint16_t color, uint8_t size) {
    if (!_initialized) return;
    char buf[16];
    sprintf(buf, "%ld", num);
    drawText(x, y, buf, color, size);
}

// ============================================================================
// POWER
// ============================================================================
void DisplayDriver::sleep() {
    if (!_initialized || _sleeping) return;
    displayOff();
    _sleeping = true;
}

void DisplayDriver::wake() {
    if (!_initialized || !_sleeping) return;
    displayOn();
    _sleeping = false;
}

// ============================================================================
// INFO
// ============================================================================
void DisplayDriver::printInfo() {
    Serial.println("\n===== STEALTH DECK DISPLAY =====");
    Serial.printf("Model: LILYGO T-Display-S3 RM67162\n");
    Serial.printf("Resolution: %dx%d (rot=%d)\n", width(), height(), _rotation);
    Serial.printf("Brightness: %d/255\n", _brightness);
    Serial.printf("Status: %s\n", _initialized ? "READY" : "INIT FAILED");
    Serial.println("================================");
}
