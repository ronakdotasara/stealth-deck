/**
 * ============================================================================
 * @file display_driver.h
 * @brief OLED Display Driver for Stealth Deck - 240×536 I2C Display
 * @version 1.0.0
 * @date 2025-11-24
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Hardware abstraction layer for the OLED display. This driver handles:
 * - I2C communication with SSD1306/SSD1351 controller
 * - Display initialization and configuration
 * - Brightness control (PWM or command-based)
 * - Frame buffer management
 * - LVGL integration as display driver
 * - Power management (sleep/wake)
 * - Hardware acceleration where available
 * 
 * ============================================================================
 * DISPLAY SPECIFICATIONS:
 * 
 * Resolution: 240×536 pixels (portrait orientation)
 * Controller: SSD1306 or compatible
 * Interface: I2C (400kHz fast mode)
 * Color Depth: Monochrome (1-bit) or 16-bit RGB565
 * I2C Address: 0x3C (default) or 0x3D (configurable)
 * Supply Voltage: 3.3V
 * Viewing Angle: 160°
 * Refresh Rate: ~60Hz max
 * 
 * ============================================================================
 * PIN CONNECTIONS:
 * 
 * Display Pin  →  ESP32 Pin
 * ────────────────────────────
 * VCC          →  3.3V
 * GND          →  GND
 * SDA          →  GPIO 21
 * SCL          →  GPIO 22
 * RES (Reset)  →  Optional
 * 
 * ============================================================================
 * MEMORY LAYOUT:
 * 
 * Frame Buffer Size: 240 × 536 × 2 bytes = 257,280 bytes (RGB565)
 * LVGL Buffer: 2 × (240 × 10) × 2 bytes = 9,600 bytes (line buffers)
 * 
 * Due to ESP32 RAM constraints, we use:
 * - Partial frame buffering (10 lines at a time)
 * - Double buffering for smooth rendering
 * - Direct I2C writes for efficiency
 * 
 * ============================================================================
 * BRIGHTNESS LEVELS:
 * 
 * STEALTH (5%):   13/255 - Calculator mode, minimal visibility
 * NORMAL (30%):   77/255 - Default unlocked mode
 * OUTDOOR (100%): 255/255 - Maximum brightness for sunlight
 * 
 * ============================================================================
 * LVGL INTEGRATION:
 * 
 * This driver provides the necessary callbacks for LVGL:
 * - lv_disp_drv_register() with flush callback
 * - rounder_cb for aligned rendering
 * - Direct pixel manipulation functions
 * 
 * ============================================================================
 * PERFORMANCE:
 * 
 * I2C Speed: 400kHz
 * Full Frame Update: ~50ms (20 FPS)
 * Partial Update: ~5ms (200 Hz small regions)
 * Power Consumption: 15-80mA depending on content
 * 
 * ============================================================================
 * USAGE EXAMPLE:
 * 
 * ```
 * DisplayDriver display;
 * 
 * void setup() {
 *     if (!display.begin(0x3C, 21, 22)) {
 *         Serial.println("Display init failed!");
 *         return;
 *     }
 *     display.setBrightness(77);  // 30%
 *     display.clear();
 *     display.drawText(10, 10, "Hello World", LV_COLOR_WHITE);
 *     display.flush();
 * }
 * ```
 * 
 * ============================================================================
 */

#ifndef DISPLAY_DRIVER_H
#define DISPLAY_DRIVER_H

#include <Arduino.h>
#include <Wire.h>
#include <lvgl.h>

// Include display controller specific library
// Choose based on your actual display controller
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ============================================================================
// CONFIGURATION CONSTANTS
// ============================================================================

// Display dimensions
#define DISPLAY_WIDTH  240
#define DISPLAY_HEIGHT 536

// I2C Configuration
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

// For monochrome displays, these map to BLACK (0) or WHITE (1)
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
 * 
 * Provides high-level interface for display operations including:
 * - Initialization and configuration
 * - Brightness control
 * - Drawing primitives (text, shapes, images)
 * - LVGL integration
 * - Power management
 */
class DisplayDriver {
public:
    // ========================================================================
    // CONSTRUCTOR & DESTRUCTOR
    // ========================================================================
    
    /**
     * @brief Constructor
     */
    DisplayDriver();
    
    /**
     * @brief Destructor - cleanup resources
     */
    ~DisplayDriver();

    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    /**
     * @brief Initialize display driver
     * 
     * @param i2c_address I2C address (typically 0x3C or 0x3D)
     * @param sda_pin SDA pin number
     * @param scl_pin SCL pin number
     * @return true if initialization successful, false otherwise
     */
    bool begin(uint8_t i2c_address = 0x3C, int sda_pin = 21, int scl_pin = 22);
    
    /**
     * @brief Initialize LVGL display driver
     * 
     * Must be called after begin()
     * 
     * @return Pointer to LVGL display driver object
     */
    lv_disp_t* initLVGL();
    
    /**
     * @brief Check if display is initialized
     * 
     * @return true if initialized, false otherwise
     */
    bool isInitialized() const { return _initialized; }

    // ========================================================================
    // DISPLAY CONTROL
    // ========================================================================
    
    /**
     * @brief Clear entire display
     * 
     * Fills display with background color (typically black)
     */
    void clear();
    
    /**
     * @brief Turn display on
     */
    void displayOn();
    
    /**
     * @brief Turn display off
     */
    void displayOff();
    
    /**
     * @brief Invert display colors
     * 
     * @param invert true to invert, false for normal
     */
    void invertDisplay(bool invert);
    
    /**
     * @brief Set display rotation
     * 
     * @param rotation Rotation value (0, 1, 2, or 3)
     */
    void setRotation(uint8_t rotation);
    
    /**
     * @brief Get current rotation
     * 
     * @return Current rotation value
     */
    uint8_t getRotation() const { return _rotation; }

    // ========================================================================
    // BRIGHTNESS CONTROL
    // ========================================================================
    
    /**
     * @brief Set display brightness
     * 
     * @param brightness Brightness value (0-255)
     */
    void setBrightness(uint8_t brightness);
    
    /**
     * @brief Get current brightness
     * 
     * @return Current brightness value (0-255)
     */
    uint8_t getBrightness() const { return _brightness; }
    
    /**
     * @brief Cycle through brightness levels
     * 
     * Cycles: STEALTH → NORMAL → OUTDOOR → STEALTH
     */
    void cycleBrightness();
    
    /**
     * @brief Fade brightness to target level
     * 
     * @param target Target brightness (0-255)
     * @param duration_ms Fade duration in milliseconds
     */
    void fadeBrightness(uint8_t target, uint16_t duration_ms);

    // ========================================================================
    // DRAWING PRIMITIVES
    // ========================================================================
    
    /**
     * @brief Draw a single pixel
     * 
     * @param x X coordinate
     * @param y Y coordinate
     * @param color Pixel color
     */
    void drawPixel(int16_t x, int16_t y, lv_color_t color);
    
    /**
     * @brief Draw a line
     * 
     * @param x0 Start X
     * @param y0 Start Y
     * @param x1 End X
     * @param y1 End Y
     * @param color Line color
     */
    void drawLine(int16_t x0, int16_t y0, int16_t x1, int16_t y1, lv_color_t color);
    
    /**
     * @brief Draw a rectangle
     * 
     * @param x Top-left X
     * @param y Top-left Y
     * @param w Width
     * @param h Height
     * @param color Border color
     */
    void drawRect(int16_t x, int16_t y, int16_t w, int16_t h, lv_color_t color);
    
    /**
     * @brief Draw a filled rectangle
     * 
     * @param x Top-left X
     * @param y Top-left Y
     * @param w Width
     * @param h Height
     * @param color Fill color
     */
    void fillRect(int16_t x, int16_t y, int16_t w, int16_t h, lv_color_t color);
    
    /**
     * @brief Draw a circle
     * 
     * @param x Center X
     * @param y Center Y
     * @param r Radius
     * @param color Circle color
     */
    void drawCircle(int16_t x, int16_t y, int16_t r, lv_color_t color);
    
    /**
     * @brief Draw a filled circle
     * 
     * @param x Center X
     * @param y Center Y
     * @param r Radius
     * @param color Fill color
     */
    void fillCircle(int16_t x, int16_t y, int16_t r, lv_color_t color);
    
    /**
     * @brief Draw text
     * 
     * @param x Start X
     * @param y Start Y
     * @param text Text string
     * @param color Text color
     * @param size Font size (1-4)
     */
    void drawText(int16_t x, int16_t y, const char* text, lv_color_t color, uint8_t size = 1);
    
    /**
     * @brief Draw bitmap image
     * 
     * @param x Top-left X
     * @param y Top-left Y
     * @param bitmap Bitmap data
     * @param w Width
     * @param h Height
     * @param color Foreground color
     */
    void drawBitmap(int16_t x, int16_t y, const uint8_t* bitmap, 
                    int16_t w, int16_t h, lv_color_t color);

    // ========================================================================
    // BUFFER MANAGEMENT
    // ========================================================================
    
    /**
     * @brief Flush buffer to display
     * 
     * Sends pending changes to display hardware
     */
    void flush();
    
    /**
     * @brief Get pointer to frame buffer
     * 
     * @return Pointer to frame buffer (use with caution)
     */
    uint8_t* getFrameBuffer() { return _frameBuffer; }
    
    /**
     * @brief Get frame buffer size
     * 
     * @return Size in bytes
     */
    size_t getFrameBufferSize() const { return _frameBufferSize; }

    // ========================================================================
    // POWER MANAGEMENT
    // ========================================================================
    
    /**
     * @brief Enter sleep mode
     * 
     * Display turns off but retains contents
     */
    void sleep();
    
    /**
     * @brief Wake from sleep mode
     */
    void wake();
    
    /**
     * @brief Check if display is in sleep mode
     * 
     * @return true if sleeping, false if awake
     */
    bool isSleeping() const { return _sleeping; }

    // ========================================================================
    // INFORMATION
    // ========================================================================
    
    /**
     * @brief Get display width
     * 
     * @return Width in pixels
     */
    int16_t getWidth() const { return _width; }
    
    /**
     * @brief Get display height
     * 
     * @return Height in pixels
     */
    int16_t getHeight() const { return _height; }
    
    /**
     * @brief Get I2C address
     * 
     * @return I2C address
     */
    uint8_t getI2CAddress() const { return _i2c_address; }
    
    /**
     * @brief Print display information to serial
     */
    void printInfo();

    // ========================================================================
    // LVGL CALLBACKS (Static)
    // ========================================================================
    
    /**
     * @brief LVGL flush callback
     * 
     * Called by LVGL to flush buffer to display
     * 
     * @param disp_drv Display driver
     * @param area Area to flush
     * @param color_p Color buffer
     */
    static void lvgl_flush_cb(lv_disp_drv_t* disp_drv, const lv_area_t* area, 
                              lv_color_t* color_p);
    
    /**
     * @brief LVGL rounder callback
     * 
     * Rounds coordinates for optimal performance
     * 
     * @param disp_drv Display driver
     * @param area Area to round
     */
    static void lvgl_rounder_cb(lv_disp_drv_t* disp_drv, lv_area_t* area);

private:
    // ========================================================================
    // PRIVATE MEMBERS
    // ========================================================================
    
    // Hardware
    uint8_t _i2c_address;           // I2C address
    int _sda_pin;                   // SDA pin
    int _scl_pin;                   // SCL pin
    TwoWire* _wire;                 // I2C interface pointer
    
    // Display properties
    int16_t _width;                 // Current width (after rotation)
    int16_t _height;                // Current height (after rotation)
    uint8_t _rotation;              // Current rotation
    uint8_t _brightness;            // Current brightness (0-255)
    bool _inverted;                 // Inverted colors
    
    // State
    bool _initialized;              // Initialization flag
    bool _sleeping;                 // Sleep mode flag
    uint8_t _powerMode;             // Current power mode
    
    // Frame buffer
    uint8_t* _frameBuffer;          // Frame buffer pointer
    size_t _frameBufferSize;        // Frame buffer size
    
    // LVGL integration
    lv_disp_drv_t _lv_disp_drv;    // LVGL display driver
    lv_disp_draw_buf_t _lv_disp_buf; // LVGL display buffer
    lv_color_t* _lv_buf1;          // LVGL buffer 1
    lv_color_t* _lv_buf2;          // LVGL buffer 2
    lv_disp_t* _lv_disp;           // LVGL display object
    
    // Performance tracking
    uint32_t _frameCount;           // Total frames rendered
    unsigned long _lastFrameTime;   // Last frame timestamp
    float _fps;                     // Current FPS
    
    // Static instance pointer for callbacks
    static DisplayDriver* _instance;
    
    // ========================================================================
    // PRIVATE METHODS
    // ========================================================================
    
    /**
     * @brief Send command to display
     * 
     * @param cmd Command byte
     * @return true if successful
     */
    bool sendCommand(uint8_t cmd);
    
    /**
     * @brief Send data to display
     * 
     * @param data Data buffer
     * @param len Length of data
     * @return true if successful
     */
    bool sendData(const uint8_t* data, size_t len);
    
    /**
     * @brief Initialize display hardware
     * 
     * @return true if successful
     */
    bool initHardware();
    
    /**
     * @brief Set display window/area
     * 
     * @param x0 Start X
     * @param y0 Start Y
     * @param x1 End X
     * @param y1 End Y
     */
    void setWindow(int16_t x0, int16_t y0, int16_t x1, int16_t y1);
    
    /**
     * @brief Update FPS counter
     */
    void updateFPS();
};

// ============================================================================
// INLINE IMPLEMENTATIONS (for performance)
// ============================================================================

/**
 * @brief Fast pixel setting (inline for speed)
 */
inline void DisplayDriver::drawPixel(int16_t x, int16_t y, lv_color_t color) {
    if (x < 0 || x >= _width || y < 0 || y >= _height) {
        return;  // Out of bounds
    }
    
    // For monochrome displays (1-bit per pixel)
    // Calculate byte position and bit position
    uint16_t byteIndex = x + (y / 8) * _width;
    uint8_t bitIndex = y % 8;
    
    if (color.full) {
        // Set pixel (white)
        _frameBuffer[byteIndex] |= (1 << bitIndex);
    } else {
        // Clear pixel (black)
        _frameBuffer[byteIndex] &= ~(1 << bitIndex);
    }
}

// ============================================================================
// GLOBAL HELPER FUNCTIONS
// ============================================================================

/**
 * @brief Convert RGB888 to RGB565
 * 
 * @param r Red (0-255)
 * @param g Green (0-255)
 * @param b Blue (0-255)
 * @return RGB565 color value
 */
inline uint16_t rgb888_to_rgb565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
}

/**
 * @brief Convert RGB565 to RGB888
 * 
 * @param color RGB565 color
 * @param r Output red (0-255)
 * @param g Output green (0-255)
 * @param b Output blue (0-255)
 */
inline void rgb565_to_rgb888(uint16_t color, uint8_t& r, uint8_t& g, uint8_t& b) {
    r = (color >> 8) & 0xF8;
    g = (color >> 3) & 0xFC;
    b = (color << 3) & 0xF8;
}

#endif // DISPLAY_DRIVER_H

// ============================================================================
// END OF FILE
// ============================================================================
