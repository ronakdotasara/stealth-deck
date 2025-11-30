/**
 * ============================================================================
 * @file display_driver.cpp
 * @brief OLED Display Driver Implementation for Stealth Deck
 * @version 1.0.0
 * @date 2025-11-30
 * @author Stealth Deck Project
 * @license MIT
 * ============================================================================
 */

#include "display_driver.h"
#include "../config.h"

// Debug logging
#ifdef DEBUG
  #define DISPLAY_DEBUG(x) DEBUG_SERIAL.print("[DISPLAY] "); DEBUG_SERIAL.println(x)
  #define DISPLAY_DEBUGF(format, ...) DEBUG_SERIAL.printf("[DISPLAY] " format "\n", __VA_ARGS__)
#else
  #define DISPLAY_DEBUG(x)
  #define DISPLAY_DEBUGF(format, ...)
#endif

// ============================================================================
// DISPLAY COMMANDS (SSD1306 Compatible)
// ============================================================================

// Fundamental Commands
#define SSD1306_SET_CONTRAST           0x81
#define SSD1306_DISPLAY_ALL_ON_RESUME  0xA4
#define SSD1306_DISPLAY_ALL_ON         0xA5
#define SSD1306_NORMAL_DISPLAY         0xA6
#define SSD1306_INVERT_DISPLAY         0xA7
#define SSD1306_DISPLAY_OFF            0xAE
#define SSD1306_DISPLAY_ON             0xAF

// Scrolling Commands
#define SSD1306_RIGHT_HORIZONTAL_SCROLL              0x26
#define SSD1306_LEFT_HORIZONTAL_SCROLL               0x27
#define SSD1306_VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL 0x29
#define SSD1306_VERTICAL_AND_LEFT_HORIZONTAL_SCROLL  0x2A
#define SSD1306_DEACTIVATE_SCROLL                    0x2E
#define SSD1306_ACTIVATE_SCROLL                      0x2F
#define SSD1306_SET_VERTICAL_SCROLL_AREA             0xA3

// Addressing Commands
#define SSD1306_SET_LOWER_COLUMN       0x00
#define SSD1306_SET_HIGHER_COLUMN      0x10
#define SSD1306_MEMORY_MODE            0x20
#define SSD1306_COLUMN_ADDR            0x21
#define SSD1306_PAGE_ADDR              0x22

// Hardware Configuration Commands
#define SSD1306_SET_START_LINE         0x40
#define SSD1306_SET_SEGMENT_REMAP      0xA0
#define SSD1306_SET_MULTIPLEX_RATIO    0xA8
#define SSD1306_COM_SCAN_INC           0xC0
#define SSD1306_COM_SCAN_DEC           0xC8
#define SSD1306_SET_DISPLAY_OFFSET     0xD3
#define SSD1306_SET_COM_PINS           0xDA

// Timing & Driving Commands
#define SSD1306_SET_DISPLAY_CLOCK_DIV  0xD5
#define SSD1306_SET_PRECHARGE          0xD9
#define SSD1306_SET_VCOM_DETECT        0xDB
#define SSD1306_CHARGE_PUMP            0x8D

// ============================================================================
// STATIC MEMBER INITIALIZATION
// ============================================================================

DisplayDriver* DisplayDriver::_instance = nullptr;

// ============================================================================
// CONSTRUCTOR
// ============================================================================

DisplayDriver::DisplayDriver() :
    _i2c_address(0x3C),
    _sda_pin(21),
    _scl_pin(22),
    _wire(&Wire),
    _width(DISPLAY_WIDTH),
    _height(DISPLAY_HEIGHT),
    _rotation(0),
    _brightness(BRIGHTNESS_NORMAL),
    _inverted(false),
    _initialized(false),
    _sleeping(false),
    _powerMode(DISPLAY_POWER_NORMAL),
    _frameBuffer(nullptr),
    _frameBufferSize(0),
    _lv_buf1(nullptr),
    _lv_buf2(nullptr),
    _lv_disp(nullptr),
    _frameCount(0),
    _lastFrameTime(0),
    _fps(0.0f)
{
    _instance = this;
}

// ============================================================================
// DESTRUCTOR
// ============================================================================

DisplayDriver::~DisplayDriver() {
    if (_frameBuffer) {
        free(_frameBuffer);
        _frameBuffer = nullptr;
    }
    
    if (_lv_buf1) {
        free(_lv_buf1);
        _lv_buf1 = nullptr;
    }
    
    if (_lv_buf2) {
        free(_lv_buf2);
        _lv_buf2 = nullptr;
    }
    
    displayOff();
    
    _initialized = false;
    _instance = nullptr;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool DisplayDriver::begin(uint8_t i2c_address, int sda_pin, int scl_pin) {
    DISPLAY_DEBUG("Initializing display...");
    
    _i2c_address = i2c_address;
    _sda_pin = sda_pin;
    _scl_pin = scl_pin;
    
    // Initialize I2C
    DISPLAY_DEBUG("  [1/5] Initializing I2C...");
    
    _wire->begin(_sda_pin, _scl_pin);
    _wire->setClock(DISPLAY_I2C_FREQUENCY);
    
    // Test I2C communication
    _wire->beginTransmission(_i2c_address);
    if (_wire->endTransmission() != 0) {
        DISPLAY_DEBUGF("  ✗ I2C device not found at address 0x%02X", _i2c_address);
        return false;
    }
    
    DISPLAY_DEBUGF("  ✓ I2C initialized at 0x%02X (%d kHz)", 
                   _i2c_address, DISPLAY_I2C_FREQUENCY / 1000);
    
    // Allocate Frame Buffer
    DISPLAY_DEBUG("  [2/5] Allocating frame buffer...");
    
    _frameBufferSize = (_width * _height) / 8;
    
    _frameBuffer = (uint8_t*)malloc(_frameBufferSize);
    if (!_frameBuffer) {
        DISPLAY_DEBUGF("  ✗ Failed to allocate %d bytes for frame buffer", _frameBufferSize);
        return false;
    }
    
    memset(_frameBuffer, 0x00, _frameBufferSize);
    
    DISPLAY_DEBUGF("  ✓ Frame buffer allocated (%d bytes)", _frameBufferSize);
    
    // Initialize Display Hardware
    DISPLAY_DEBUG("  [3/5] Initializing display hardware...");
    
    if (!initHardware()) {
        DISPLAY_DEBUG("  ✗ Hardware initialization failed");
        free(_frameBuffer);
        _frameBuffer = nullptr;
        return false;
    }
    
    DISPLAY_DEBUG("  ✓ Hardware initialized");
    
    // Clear Display
    DISPLAY_DEBUG("  [4/5] Clearing display...");
    clear();
    flush();
    DISPLAY_DEBUG("  ✓ Display cleared");
    
    // Turn On Display
    DISPLAY_DEBUG("  [5/5] Turning on display...");
    displayOn();
    setBrightness(_brightness);
    DISPLAY_DEBUG("  ✓ Display on");
    
    _initialized = true;
    _lastFrameTime = millis();
    
    DISPLAY_DEBUG("✓ Display initialization complete!");
    printInfo();
    
    return true;
}

lv_disp_t* DisplayDriver::initLVGL() {
    if (!_initialized) {
        DISPLAY_DEBUG("ERROR: Display not initialized. Call begin() first.");
        return nullptr;
    }
    
    DISPLAY_DEBUG("Initializing LVGL...");
    
    // Allocate LVGL Buffers
    DISPLAY_DEBUG("  [1/3] Allocating LVGL buffers...");
    
    size_t bufferSize = LVGL_BUFFER_SIZE * sizeof(lv_color_t);
    
    _lv_buf1 = (lv_color_t*)heap_caps_malloc(bufferSize, MALLOC_CAP_DMA);
    if (!_lv_buf1) {
        DISPLAY_DEBUGF("  ✗ Failed to allocate LVGL buffer 1 (%d bytes)", bufferSize);
        return nullptr;
    }
    
    _lv_buf2 = (lv_color_t*)heap_caps_malloc(bufferSize, MALLOC_CAP_DMA);
    if (!_lv_buf2) {
        DISPLAY_DEBUGF("  ✗ Failed to allocate LVGL buffer 2 (%d bytes)", bufferSize);
        free(_lv_buf1);
        _lv_buf1 = nullptr;
        return nullptr;
    }
    
    DISPLAY_DEBUGF("  ✓ LVGL buffers allocated (2 × %d bytes)", bufferSize);
    
    // Initialize LVGL Display Buffer
    DISPLAY_DEBUG("  [2/3] Initializing LVGL display buffer...");
    
    lv_disp_draw_buf_init(&_lv_disp_buf, _lv_buf1, _lv_buf2, LVGL_BUFFER_SIZE);
    
    DISPLAY_DEBUG("  ✓ LVGL display buffer initialized");
    
    // Register Display Driver
    DISPLAY_DEBUG("  [3/3] Registering LVGL display driver...");
    
    lv_disp_drv_init(&_lv_disp_drv);
    
    _lv_disp_drv.hor_res = _width;
    _lv_disp_drv.ver_res = _height;
    _lv_disp_drv.flush_cb = lvgl_flush_cb;
    _lv_disp_drv.rounder_cb = lvgl_rounder_cb;
    _lv_disp_drv.draw_buf = &_lv_disp_buf;
    _lv_disp_drv.user_data = this;
    
    _lv_disp = lv_disp_drv_register(&_lv_disp_drv);
    
    if (!_lv_disp) {
        DISPLAY_DEBUG("  ✗ Failed to register LVGL display driver");
        free(_lv_buf1);
        free(_lv_buf2);
        _lv_buf1 = nullptr;
        _lv_buf2 = nullptr;
        return nullptr;
    }
    
    DISPLAY_DEBUG("  ✓ LVGL display driver registered");
    DISPLAY_DEBUG("✓ LVGL initialization complete!");
    
    return _lv_disp;
}

bool DisplayDriver::initHardware() {
    if (!sendCommand(SSD1306_DISPLAY_OFF)) return false;
    if (!sendCommand(SSD1306_SET_DISPLAY_CLOCK_DIV)) return false;
    if (!sendCommand(0x80)) return false;
    if (!sendCommand(SSD1306_SET_MULTIPLEX_RATIO)) return false;
    if (!sendCommand(_height - 1)) return false;
    if (!sendCommand(SSD1306_SET_DISPLAY_OFFSET)) return false;
    if (!sendCommand(0x00)) return false;
    if (!sendCommand(SSD1306_SET_START_LINE | 0x0)) return false;
    if (!sendCommand(SSD1306_CHARGE_PUMP)) return false;
    if (!sendCommand(0x14)) return false;
    if (!sendCommand(SSD1306_MEMORY_MODE)) return false;
    if (!sendCommand(0x00)) return false;
    if (!sendCommand(SSD1306_SET_SEGMENT_REMAP | 0x1)) return false;
    if (!sendCommand(SSD1306_COM_SCAN_DEC)) return false;
    if (!sendCommand(SSD1306_SET_COM_PINS)) return false;
    if (!sendCommand(0x12)) return false;
    if (!sendCommand(SSD1306_SET_CONTRAST)) return false;
    if (!sendCommand(0x7F)) return false;
    if (!sendCommand(SSD1306_SET_PRECHARGE)) return false;
    if (!sendCommand(0xF1)) return false;
    if (!sendCommand(SSD1306_SET_VCOM_DETECT)) return false;
    if (!sendCommand(0x40)) return false;
    if (!sendCommand(SSD1306_DISPLAY_ALL_ON_RESUME)) return false;
    if (!sendCommand(SSD1306_NORMAL_DISPLAY)) return false;
    if (!sendCommand(SSD1306_DEACTIVATE_SCROLL)) return false;
    
    return true;
}

// ============================================================================
// DISPLAY CONTROL
// ============================================================================

void DisplayDriver::clear() {
    if (!_initialized) return;
    memset(_frameBuffer, 0x00, _frameBufferSize);
}

void DisplayDriver::displayOn() {
    if (!_initialized) return;
    sendCommand(SSD1306_DISPLAY_ON);
    _powerMode = DISPLAY_POWER_NORMAL;
    _sleeping = false;
    DISPLAY_DEBUG("Display ON");
}

void DisplayDriver::displayOff() {
    if (!_initialized) return;
    sendCommand(SSD1306_DISPLAY_OFF);
    _powerMode = DISPLAY_POWER_OFF;
    DISPLAY_DEBUG("Display OFF");
}

void DisplayDriver::invertDisplay(bool invert) {
    if (!_initialized) return;
    _inverted = invert;
    sendCommand(invert ? SSD1306_INVERT_DISPLAY : SSD1306_NORMAL_DISPLAY);
    DISPLAY_DEBUGF("Display %s", invert ? "INVERTED" : "NORMAL");
}

void DisplayDriver::setRotation(uint8_t rotation) {
    _rotation = rotation % 4;
    if (_rotation == 1 || _rotation == 3) {
        int16_t temp = _width;
        _width = _height;
        _height = temp;
    }
    DISPLAY_DEBUGF("Rotation set to %d", _rotation);
}

// ============================================================================
// BRIGHTNESS CONTROL
// ============================================================================

void DisplayDriver::setBrightness(uint8_t brightness) {
    if (!_initialized) return;
    _brightness = brightness;
    sendCommand(SSD1306_SET_CONTRAST);
    sendCommand(brightness);
    DISPLAY_DEBUGF("Brightness set to %d (%d%%)", brightness, (brightness * 100) / 255);
}

void DisplayDriver::cycleBrightness() {
    if (_brightness == BRIGHTNESS_STEALTH) {
        setBrightness(BRIGHTNESS_NORMAL);
    } else if (_brightness == BRIGHTNESS_NORMAL) {
        setBrightness(BRIGHTNESS_OUTDOOR);
    } else {
        setBrightness(BRIGHTNESS_STEALTH);
    }
}

void DisplayDriver::fadeBrightness(uint8_t target, uint16_t duration_ms) {
    int16_t steps = abs((int16_t)target - (int16_t)_brightness);
    if (steps == 0) return;
    
    int16_t stepDelay = duration_ms / steps;
    int16_t direction = (target > _brightness) ? 1 : -1;
    
    for (int16_t i = 0; i < steps; i++) {
        _brightness += direction;
        setBrightness(_brightness);
        delay(stepDelay);
    }
    
    setBrightness(target);
}

// ============================================================================
// DRAWING PRIMITIVES - INCLUDING DRAWPIXEL
// ============================================================================

/**
 * @brief Draw a single pixel
 * @param x X coordinate
 * @param y Y coordinate  
 * @param color Pixel color
 */
void DisplayDriver::drawPixel(int16_t x, int16_t y, lv_color_t color) {
    if (!_initialized || !_frameBuffer) return;
    
    // Bounds checking
    if (x < 0 || x >= _width || y < 0 || y >= _height) return;
    
    // Calculate byte position in frame buffer
    uint16_t byteIndex = x + (y / 8) * _width;
    uint8_t bitMask = 1 << (y % 8);
    
    // Set or clear pixel based on color
    if (color.full) {  // White/On
        _frameBuffer[byteIndex] |= bitMask;
    } else {  // Black/Off
        _frameBuffer[byteIndex] &= ~bitMask;
    }
}

void DisplayDriver::drawLine(int16_t x0, int16_t y0, int16_t x1, int16_t y1, lv_color_t color) {
    int16_t dx = abs(x1 - x0);
    int16_t dy = abs(y1 - y0);
    int16_t sx = (x0 < x1) ? 1 : -1;
    int16_t sy = (y0 < y1) ? 1 : -1;
    int16_t err = dx - dy;
    
    while (true) {
        drawPixel(x0, y0, color);
        
        if (x0 == x1 && y0 == y1) break;
        
        int16_t e2 = 2 * err;
        if (e2 > -dy) {
            err -= dy;
            x0 += sx;
        }
        if (e2 < dx) {
            err += dx;
            y0 += sy;
        }
    }
}

void DisplayDriver::drawRect(int16_t x, int16_t y, int16_t w, int16_t h, lv_color_t color) {
    drawLine(x, y, x + w - 1, y, color);
    drawLine(x, y + h - 1, x + w - 1, y + h - 1, color);
    drawLine(x, y, x, y + h - 1, color);
    drawLine(x + w - 1, y, x + w - 1, y + h - 1, color);
}

void DisplayDriver::fillRect(int16_t x, int16_t y, int16_t w, int16_t h, lv_color_t color) {
    for (int16_t i = y; i < y + h; i++) {
        drawLine(x, i, x + w - 1, i, color);
    }
}

void DisplayDriver::drawCircle(int16_t x0, int16_t y0, int16_t r, lv_color_t color) {
    int16_t x = r;
    int16_t y = 0;
    int16_t err = 0;
    
    while (x >= y) {
        drawPixel(x0 + x, y0 + y, color);
        drawPixel(x0 + y, y0 + x, color);
        drawPixel(x0 - y, y0 + x, color);
        drawPixel(x0 - x, y0 + y, color);
        drawPixel(x0 - x, y0 - y, color);
        drawPixel(x0 - y, y0 - x, color);
        drawPixel(x0 + y, y0 - x, color);
        drawPixel(x0 + x, y0 - y, color);
        
        if (err <= 0) {
            y += 1;
            err += 2 * y + 1;
        }
        if (err > 0) {
            x -= 1;
            err -= 2 * x + 1;
        }
    }
}

void DisplayDriver::fillCircle(int16_t x0, int16_t y0, int16_t r, lv_color_t color) {
    for (int16_t y = -r; y <= r; y++) {
        for (int16_t x = -r; x <= r; x++) {
            if (x * x + y * y <= r * r) {
                drawPixel(x0 + x, y0 + y, color);
            }
        }
    }
}

void DisplayDriver::drawText(int16_t x, int16_t y, const char* text, lv_color_t color, uint8_t size) {
    DISPLAY_DEBUGF("Text drawing at (%d,%d): %s", x, y, text);
    // Use LVGL for text rendering in production
}

void DisplayDriver::drawBitmap(int16_t x, int16_t y, const uint8_t* bitmap, 
                               int16_t w, int16_t h, lv_color_t color) {
    for (int16_t j = 0; j < h; j++) {
        for (int16_t i = 0; i < w; i++) {
            uint16_t byteIndex = i / 8 + j * ((w + 7) / 8);
            uint8_t bitIndex = 7 - (i % 8);
            
            if (bitmap[byteIndex] & (1 << bitIndex)) {
                drawPixel(x + i, y + j, color);
            }
        }
    }
}

// ============================================================================
// BUFFER MANAGEMENT
// ============================================================================

void DisplayDriver::flush() {
    if (!_initialized || !_frameBuffer) return;
    
    sendCommand(SSD1306_COLUMN_ADDR);
    sendCommand(0);
    sendCommand(_width - 1);
    
    sendCommand(SSD1306_PAGE_ADDR);
    sendCommand(0);
    sendCommand((_height / 8) - 1);
    
    sendData(_frameBuffer, _frameBufferSize);
    
    updateFPS();
}

// ============================================================================
// POWER MANAGEMENT
// ============================================================================

void DisplayDriver::sleep() {
    if (!_initialized || _sleeping) return;
    displayOff();
    _sleeping = true;
    _powerMode = DISPLAY_POWER_SLEEP;
    DISPLAY_DEBUG("Entered sleep mode");
}

void DisplayDriver::wake() {
    if (!_initialized || !_sleeping) return;
    displayOn();
    _sleeping = false;
    _powerMode = DISPLAY_POWER_NORMAL;
    DISPLAY_DEBUG("Woke from sleep mode");
}

// ============================================================================
// INFORMATION
// ============================================================================

void DisplayDriver::printInfo() {
    #ifdef DEBUG
    DEBUG_SERIAL.println("\n===== DISPLAY INFO =====");
    DEBUG_SERIAL.printf("Resolution: %d × %d\n", _width, _height);
    DEBUG_SERIAL.printf("I2C Address: 0x%02X\n", _i2c_address);
    DEBUG_SERIAL.printf("I2C Frequency: %d kHz\n", DISPLAY_I2C_FREQUENCY / 1000);
    DEBUG_SERIAL.printf("Frame Buffer: %d bytes\n", _frameBufferSize);
    DEBUG_SERIAL.printf("Brightness: %d (%d%%)\n", _brightness, (_brightness * 100) / 255);
    DEBUG_SERIAL.printf("Rotation: %d\n", _rotation);
    DEBUG_SERIAL.printf("Power Mode: %d\n", _powerMode);
    DEBUG_SERIAL.printf("FPS: %.1f\n", _fps);
    DEBUG_SERIAL.println("========================\n");
    #endif
}

// ============================================================================
// LVGL CALLBACKS
// ============================================================================

void DisplayDriver::lvgl_flush_cb(lv_disp_drv_t* disp_drv, const lv_area_t* area, 
                                  lv_color_t* color_p) {
    DisplayDriver* driver = (DisplayDriver*)disp_drv->user_data;
    if (!driver || !driver->_initialized) {
        lv_disp_flush_ready(disp_drv);
        return;
    }
    
    int32_t w = area->x2 - area->x1 + 1;
    int32_t h = area->y2 - area->y1 + 1;
    
    DISPLAY_DEBUGF("LVGL Flush: (%d,%d) to (%d,%d) - %dx%d pixels", 
                   area->x1, area->y1, area->x2, area->y2, w, h);
    
    driver->setWindow(area->x1, area->y1, area->x2, area->y2);
    
    uint8_t* buf = (uint8_t*)color_p;
    size_t size = w * h * sizeof(lv_color_t);
    driver->sendData(buf, size);
    
    lv_disp_flush_ready(disp_drv);
    
    driver->updateFPS();
}

void DisplayDriver::lvgl_rounder_cb(lv_disp_drv_t* disp_drv, lv_area_t* area) {
    area->y1 = (area->y1 / 8) * 8;
    area->y2 = ((area->y2 + 7) / 8) * 8 - 1;
}

// ============================================================================
// PRIVATE METHODS
// ============================================================================

bool DisplayDriver::sendCommand(uint8_t cmd) {
    _wire->beginTransmission(_i2c_address);
    _wire->write(0x00);
    _wire->write(cmd);
    return (_wire->endTransmission() == 0);
}

bool DisplayDriver::sendData(const uint8_t* data, size_t len) {
    const size_t chunkSize = 32;
    
    for (size_t i = 0; i < len; i += chunkSize) {
        size_t remaining = len - i;
        size_t toSend = (remaining < chunkSize) ? remaining : chunkSize;
        
        _wire->beginTransmission(_i2c_address);
        _wire->write(0x40);
        
        for (size_t j = 0; j < toSend; j++) {
            _wire->write(data[i + j]);
        }
        
        if (_wire->endTransmission() != 0) {
            return false;
        }
    }
    
    return true;
}

void DisplayDriver::setWindow(int16_t x0, int16_t y0, int16_t x1, int16_t y1) {
    sendCommand(SSD1306_COLUMN_ADDR);
    sendCommand(x0);
    sendCommand(x1);
    
    sendCommand(SSD1306_PAGE_ADDR);
    sendCommand(y0 / 8);
    sendCommand(y1 / 8);
}

void DisplayDriver::updateFPS() {
    _frameCount++;
    
    unsigned long now = millis();
    unsigned long elapsed = now - _lastFrameTime;
    
    if (elapsed >= 1000) {
        _fps = (_frameCount * 1000.0f) / elapsed;
        _frameCount = 0;
        _lastFrameTime = now;
    }
}

// ============================================================================
// END OF FILE
// ============================================================================
