/**
 * ============================================================================
 * ui_renderer.h - Advanced UI Renderer
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-25
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Advanced UI rendering engine for OLED display.
 * Handles complex layouts, widgets, and animations.
 * 
 * Features:
 * - Widget system
 * - Layout management
 * - Icons and bitmaps
 * - Progress bars
 * - Scrollable text
 * - Status indicators
 * 
 * ============================================================================
 */

#ifndef UI_RENDERER_H
#define UI_RENDERER_H

#include <Arduino.h>
#include "display_driver.h"

#define MAX_WIDGETS 10

enum WidgetType {
    WIDGET_LABEL,
    WIDGET_ICON,
    WIDGET_PROGRESS_BAR,
    WIDGET_BUTTON,
    WIDGET_SCROLLABLE_TEXT
};

enum Alignment {
    ALIGN_LEFT,
    ALIGN_CENTER,
    ALIGN_RIGHT
};

struct Widget {
    WidgetType type;
    uint16_t x;
    uint16_t y;
    uint16_t width;
    uint16_t height;
    bool visible;
    void* data;
};

struct Label {
    char text[64];
    uint8_t fontSize;
    Alignment align;
};

struct Icon {
    const uint8_t* bitmap;
    uint16_t width;
    uint16_t height;
};

struct ProgressBar {
    uint8_t progress;
    bool showPercentage;
};

struct ScrollableText {
    char* text;
    uint16_t scrollOffset;
    uint16_t maxScroll;
};

class UIRenderer {
public:
    UIRenderer(DisplayDriver* display);
    
    void begin();
    void render();
    void clear();
    
    // Widget management
    int16_t addWidget(WidgetType type, uint16_t x, uint16_t y);
    bool removeWidget(int16_t id);
    bool setWidgetVisible(int16_t id, bool visible);
    
    // Label widgets
    bool setLabelText(int16_t id, const char* text);
    bool setLabelSize(int16_t id, uint8_t size);
    bool setLabelAlignment(int16_t id, Alignment align);
    
    // Icon widgets
    bool setIcon(int16_t id, const uint8_t* bitmap, uint16_t w, uint16_t h);
    
    // Progress bar widgets
    bool setProgress(int16_t id, uint8_t progress);
    bool setProgressShowPercentage(int16_t id, bool show);
    
    // Scrollable text widgets
    bool setScrollableText(int16_t id, const char* text);
    bool scrollText(int16_t id, int16_t offset);
    
    // Drawing helpers
    void drawStatusBar();
    void drawBatteryIcon(uint16_t x, uint16_t y, uint8_t percentage);
    void drawSignalIcon(uint16_t x, uint16_t y, uint8_t strength);
    void drawFrame(uint16_t x, uint16_t y, uint16_t w, uint16_t h);
    
    // Animations
    void fadeIn(uint16_t duration);
    void fadeOut(uint16_t duration);
    void slideIn(uint16_t duration, bool fromLeft);
    
private:
    DisplayDriver* display;
    
    Widget widgets[MAX_WIDGETS];
    uint8_t widgetCount;
    
    void renderWidget(Widget* widget);
    void renderLabel(Widget* widget);
    void renderIcon(Widget* widget);
    void renderProgressBar(Widget* widget);
    void renderScrollableText(Widget* widget);
    
    int16_t getWidgetIndex(int16_t id);
};

#endif
