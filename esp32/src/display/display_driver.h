/**
 * @file display_driver.h - LILYGO T-Display-S3 RM67162 (170×320)
 * @version 1.1.0 | LILYGO OFFICIAL LIBRARY (FIXES BLACK SCREEN)
 */

#ifndef DISPLAY_DRIVER_H
#define DISPLAY_DRIVER_H

#include <Arduino.h>
#include <LilyGo_TDisplay_S3.h>  // ✅ OFFICIAL LIBRARY
#include "../config.h"

class DisplayDriver {
public:
    DisplayDriver();
    ~DisplayDriver();

    bool begin();
    bool isInitialized() const { return _initialized; }

    void clear(uint16_t color = COLOR_BLACK);
    void fillScreen(uint16_t color);
    void displayOn();
    void displayOff();
    void setRotation(uint8_t rotation);
    uint8_t getRotation() const { return _rotation; }
    uint8_t getBrightness() const { return _brightness; }

    void setBrightness(uint8_t brightness);
    void cycleBrightness();
    void fadeToBlack(uint16_t duration_ms);

    // Drawing (LilyGo compatible)
    void drawPixel(int16_t x, int16_t y, uint16_t color);
    void drawRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color);
    void fillRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color);

    // Text (Simplified for LilyGo)
    void drawText(int x, int y, const char* text, uint16_t color, uint8_t size = 2);
    void drawNumber(int x, int y, long num, uint16_t color, uint8_t size = 2);

    int16_t width() const { return 170; }   // Landscape
    int16_t height() const { return 320; }

    void printInfo();
    void sleep();
    void wake();
    bool isSleeping() const { return _sleeping; }

private:
    LilyGo_TDisplay_S3 _tft = LilyGo_TDisplay_S3();  // ✅ OFFICIAL
    uint8_t _rotation = 1;
    uint8_t _brightness = 128;
    bool _initialized = false;
    bool _sleeping = false;
    
    void initBacklight();
};

extern DisplayDriver display;

inline uint16_t rgb888_to_rgb565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
}

#endif
