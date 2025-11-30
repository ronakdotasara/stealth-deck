/**
 * ============================================================================
 * @file display_driver.h
 * @brief OLED Display Driver for Stealth Deck - 240×536 I2C Display
 * @version 1.0.0
 * @date 2025-11-30
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * [Rest of your header comments stay the same]
 * ============================================================================
 */


#ifndef DISPLAY_DRIVER_H
#define DISPLAY_DRIVER_H


#include <Arduino.h>
#include <Wire.h>
#include <lvgl.h>

// Note: For LILYGO T-Display-S3 AMOLED, we use the LilyGo library instead
// Commenting out Adafruit libraries
// #include <Adafruit_GFX.h>
// #include <Adafruit_SSD1306.h>


// ============================================================================
// CONFIGURATION CONSTANTS
// ============================================================================


// Display dimensions (for T-Display-S3 AMOLED)
#define DISPLAY_WIDTH  240
#define DISPLAY_HEIGHT 536


// I2C Configuration (not used for T-Display-S3 AMOLED - uses SPI)
#define DISPLAY_I2C_FREQUENCY 400000  // 400kHz fast mode
#define DISPLAY_I2C_TIMEOUT 1000      // 1 second timeout


// LVGL Buffer Configuration
#define LVGL_BUFFER_LINES 10          // Number of lines per buffer
#define LVGL_BUFFER_SIZE (DISPLAY_WIDTH * LVGL_BUFFER_LINES)


// Brightness levels
#define BRIGHTNESS_MIN 0
#define BRIGHTNESS_STEALTH 13         // 5%
#define BRIGHTNESS_NORMAL 77          // 30%
#define BRIGHTNESS_OUTDOOR 255        // 100%
#define BRIGHTNESS_MAX 255


// Display rotation
#define DISPLAY_ROTATION_0   0        // Portrait
#define DISPLAY_ROTATION_90  1        // Landscape
#define DISPLAY_ROTATION_180 2        // Portrait inverted
#define DISPLAY_ROTATION_270 3        // Landscape inverted


// Power modes
#define DISPLAY_POWER_NORMAL 0
#define DISPLAY_POWER_SLEEP 1
#define DISPLAY_POWER_OFF 2


// ============================================================================
// COLOR DEFINITIONS (RGB565 format for 16-bit displays)
// ============================================================================


// For 16-bit color displays
#define COLOR_BLACK   lv_color_hex(0x000000)
#define COLOR_WHITE   lv_color_hex(0xFFFFFF)
#define COLOR_RED     lv_color_hex(0xFF0000)
#define COLOR_GREEN   lv_color_hex(0x00FF00)
#define COLOR_BLUE    lv_color_hex(0x0000FF)
#define COLOR_YELLOW  lv_color_hex(0xFFFF00)
#define COLOR_CYAN    lv_color_hex(0x00FFFF)
#define COLOR_MAGENTA lv_color_hex(0xFF00FF)
#define COLOR_GRAY    lv_color_hex(0x808080)


// ============================================================================
// CLASS DEFINITION
// ============================================================================


/**
 * @class DisplayDriver
 * @brief Hardware abstraction layer for OLED display
 */
class DisplayDriver {
public:
    // ========================================================================
    // CONSTRUCTOR & DESTRUCTOR
    // ========================================================================
    
    DisplayDriver();
    ~DisplayDriver();


    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    bool begin(uint8_t i2c_address = 0x3C, int sda_pin = 21, int scl_pin = 22);
    lv_disp_t* initLVGL();
    bool isInitialized() const { return _initialized; }


    // ========================================================================
    // DISPLAY CONTROL
    // ========================================================================
    
    void clear();
    void displayOn();
    void displayOff();
    void invertDisplay(bool invert);
    void setRotation(uint8_t rotation);
    uint8_t getRotation() const { return _rotation; }


    // ========================================================================
    // BRIGHTNESS CONTROL
    // ========================================================================
    
    void setBrightness(uint8_t brightness);
    uint8_t getBrightness() const { return _brightness; }
    void cycleBrightness();
    void fadeBrightness(uint8_t target, uint16_t duration_ms);


    // ========================================================================
    // DRAWING PRIMITIVES
    // ========================================================================
    
    void drawPixel(int16_t x, int16_t y, lv_color_t color);
    void drawLine(int16_t x0, int16_t y0, int16_t x1, int16_t y1, lv_color_t color);
    void drawRect(int16_t x, int16_t y, int16_t w, int16_t h, lv_color_t color);
    void fillRect(int16_t x, int16_t y, int16_t w, int16_t h, lv_color_t color);
    void drawCircle(int16_t x, int16_t y, int16_t r, lv_color_t color);
    void fillCircle(int16_t x, int16_t y, int16_t r, lv_color_t color);
    void drawText(int16_t x, int16_t y, const char* text, lv_color_t color, uint8_t size = 1);
    void drawBitmap(int16_t x, int16_t y, const uint8_t* bitmap, 
                    int16_t w, int16_t h, lv_color_t color);


    // ========================================================================
    // BUFFER MANAGEMENT
    // ========================================================================
    
    void flush();
    uint8_t* getFrameBuffer() { return _frameBuffer; }
    size_t getFrameBufferSize() const { return _frameBufferSize; }


    // ========================================================================
    // POWER MANAGEMENT
    // ========================================================================
    
    void sleep();
    void wake();
    bool isSleeping() const { return _sleeping; }


    // ========================================================================
    // INFORMATION
    // ========================================================================
    
    int16_t getWidth() const { return _width; }
    int16_t getHeight() const { return _height; }
    uint8_t getI2CAddress() const { return _i2c_address; }
    void printInfo();


    // ========================================================================
    // LVGL CALLBACKS (Static)
    // ========================================================================
    
    static void lvgl_flush_cb(lv_disp_drv_t* disp_drv, const lv_area_t* area, 
                              lv_color_t* color_p);
    static void lvgl_rounder_cb(lv_disp_drv_t* disp_drv, lv_area_t* area);


private:
    // ========================================================================
    // PRIVATE MEMBERS
    // ========================================================================
    
    uint8_t _i2c_address;
    int _sda_pin;
    int _scl_pin;
    TwoWire* _wire;
    
    int16_t _width;
    int16_t _height;
    uint8_t _rotation;
    uint8_t _brightness;
    bool _inverted;
    
    bool _initialized;
    bool _sleeping;
    uint8_t _powerMode;
    
    uint8_t* _frameBuffer;
    size_t _frameBufferSize;
    
    lv_disp_drv_t _lv_disp_drv;
    lv_disp_draw_buf_t _lv_disp_buf;
    lv_color_t* _lv_buf1;
    lv_color_t* _lv_buf2;
    lv_disp_t* _lv_disp;
    
    uint32_t _frameCount;
    unsigned long _lastFrameTime;
    float _fps;
    
    static DisplayDriver* _instance;
    
    // ========================================================================
    // PRIVATE METHODS
    // ========================================================================
    
    bool sendCommand(uint8_t cmd);
    bool sendData(const uint8_t* data, size_t len);
    bool initHardware();
    void setWindow(int16_t x0, int16_t y0, int16_t x1, int16_t y1);
    void updateFPS();
};


// ============================================================================
// GLOBAL HELPER FUNCTIONS
// ============================================================================


inline uint16_t rgb888_to_rgb565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
}

inline void rgb565_to_rgb888(uint16_t color, uint8_t& r, uint8_t& g, uint8_t& b) {
    r = (color >> 8) & 0xF8;
    g = (color >> 3) & 0xFC;
    b = (color << 3) & 0xF8;
}


#endif // DISPLAY_DRIVER_H
