/**
 * ============================================================================
 * ui_renderer.cpp - UI Renderer Implementation
 * ============================================================================
 */

#include "ui_renderer.h"

UIRenderer::UIRenderer(DisplayDriver* disp) {
    display = disp;
    widgetCount = 0;
    
    memset(widgets, 0, sizeof(widgets));
}

void UIRenderer::begin() {
    Serial.println("UI Renderer initialized");
}

void UIRenderer::render() {
    display->clear();
    
    for (uint8_t i = 0; i < widgetCount; i++) {
        if (widgets[i].visible) {
            renderWidget(&widgets[i]);
        }
    }
    
    display->flush();  // FIXED: Use flush() instead of display()
}

void UIRenderer::clear() {
    display->clear();
}

int16_t UIRenderer::addWidget(WidgetType type, uint16_t x, uint16_t y) {
    if (widgetCount >= MAX_WIDGETS) {
        return -1;
    }
    
    int16_t id = widgetCount;
    
    widgets[id].type = type;
    widgets[id].x = x;
    widgets[id].y = y;
    widgets[id].visible = true;
    
    switch (type) {
        case WIDGET_LABEL: {
            Label* label = new Label();
            memset(label->text, 0, sizeof(label->text));
            label->fontSize = 1;
            label->align = ALIGN_LEFT;
            widgets[id].data = label;
            widgets[id].width = 100;
            widgets[id].height = 8;
            break;
        }
        
        case WIDGET_ICON: {
            Icon* icon = new Icon();
            icon->bitmap = nullptr;
            icon->width = 16;
            icon->height = 16;
            widgets[id].data = icon;
            widgets[id].width = 16;
            widgets[id].height = 16;
            break;
        }
        
        case WIDGET_PROGRESS_BAR: {
            ProgressBar* bar = new ProgressBar();
            bar->progress = 0;
            bar->showPercentage = true;
            widgets[id].data = bar;
            widgets[id].width = 100;
            widgets[id].height = 10;
            break;
        }
        
        case WIDGET_SCROLLABLE_TEXT: {
            ScrollableText* text = new ScrollableText();
            text->text = nullptr;
            text->scrollOffset = 0;
            text->maxScroll = 0;
            widgets[id].data = text;
            widgets[id].width = 240;
            widgets[id].height = 100;
            break;
        }
        
        default:
            break;
    }
    
    widgetCount++;
    
    return id;
}

bool UIRenderer::removeWidget(int16_t id) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0) {
        return false;
    }
    
    if (widgets[index].data) {
        free(widgets[index].data);
    }
    
    for (uint8_t i = index; i < widgetCount - 1; i++) {
        widgets[i] = widgets[i + 1];
    }
    
    widgetCount--;
    
    return true;
}

bool UIRenderer::setWidgetVisible(int16_t id, bool visible) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0) {
        return false;
    }
    
    widgets[index].visible = visible;
    
    return true;
}

bool UIRenderer::setLabelText(int16_t id, const char* text) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0 || widgets[index].type != WIDGET_LABEL) {
        return false;
    }
    
    Label* label = (Label*)widgets[index].data;
    strncpy(label->text, text, sizeof(label->text) - 1);
    
    return true;
}

bool UIRenderer::setLabelSize(int16_t id, uint8_t size) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0 || widgets[index].type != WIDGET_LABEL) {
        return false;
    }
    
    Label* label = (Label*)widgets[index].data;
    label->fontSize = size;
    
    return true;
}

bool UIRenderer::setLabelAlignment(int16_t id, Alignment align) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0 || widgets[index].type != WIDGET_LABEL) {
        return false;
    }
    
    Label* label = (Label*)widgets[index].data;
    label->align = align;
    
    return true;
}

bool UIRenderer::setIcon(int16_t id, const uint8_t* bitmap, uint16_t w, uint16_t h) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0 || widgets[index].type != WIDGET_ICON) {
        return false;
    }
    
    Icon* icon = (Icon*)widgets[index].data;
    icon->bitmap = bitmap;
    icon->width = w;
    icon->height = h;
    
    widgets[index].width = w;
    widgets[index].height = h;
    
    return true;
}

bool UIRenderer::setProgress(int16_t id, uint8_t progress) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0 || widgets[index].type != WIDGET_PROGRESS_BAR) {
        return false;
    }
    
    ProgressBar* bar = (ProgressBar*)widgets[index].data;
    bar->progress = min(progress, (uint8_t)100);
    
    return true;
}

bool UIRenderer::setProgressShowPercentage(int16_t id, bool show) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0 || widgets[index].type != WIDGET_PROGRESS_BAR) {
        return false;
    }
    
    ProgressBar* bar = (ProgressBar*)widgets[index].data;
    bar->showPercentage = show;
    
    return true;
}

bool UIRenderer::setScrollableText(int16_t id, const char* text) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0 || widgets[index].type != WIDGET_SCROLLABLE_TEXT) {
        return false;
    }
    
    ScrollableText* scrollText = (ScrollableText*)widgets[index].data;
    
    if (scrollText->text) {
        free(scrollText->text);
    }
    
    scrollText->text = strdup(text);
    scrollText->scrollOffset = 0;
    scrollText->maxScroll = strlen(text) * 6;
    
    return true;
}

bool UIRenderer::scrollText(int16_t id, int16_t offset) {
    int16_t index = getWidgetIndex(id);
    
    if (index < 0 || widgets[index].type != WIDGET_SCROLLABLE_TEXT) {
        return false;
    }
    
    ScrollableText* scrollText = (ScrollableText*)widgets[index].data;
    
    scrollText->scrollOffset += offset;
    
    if (scrollText->scrollOffset < 0) {
        scrollText->scrollOffset = 0;
    }
    
    if (scrollText->scrollOffset > scrollText->maxScroll) {
        scrollText->scrollOffset = scrollText->maxScroll;
    }
    
    return true;
}

void UIRenderer::drawStatusBar() {
    // FIXED: Draw line with color
    display->drawLine(0, 15, 240, 15, COLOR_WHITE);
    
    // FIXED: Draw time with color
    display->drawText(5, 2, "12:34", COLOR_WHITE, 1);
    
    // Draw battery icon
    drawBatteryIcon(200, 2, 75);
    
    // Draw signal icon
    drawSignalIcon(220, 2, 3);
}

void UIRenderer::drawBatteryIcon(uint16_t x, uint16_t y, uint8_t percentage) {
    // FIXED: Add color parameters
    display->drawRect(x, y, 20, 10, COLOR_WHITE);
    display->drawRect(x + 20, y + 3, 2, 4, COLOR_WHITE);
    
    uint8_t fillWidth = (percentage * 18) / 100;
    display->fillRect(x + 1, y + 1, fillWidth, 8, COLOR_WHITE);
}

void UIRenderer::drawSignalIcon(uint16_t x, uint16_t y, uint8_t strength) {
    for (uint8_t i = 0; i < strength; i++) {
        uint8_t h = (i + 1) * 3;
        // FIXED: Add color parameter
        display->fillRect(x + i * 4, y + (12 - h), 3, h, COLOR_WHITE);
    }
}

void UIRenderer::drawFrame(uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
    // FIXED: Add color parameter
    display->drawRect(x, y, w, h, COLOR_WHITE);
}

void UIRenderer::renderWidget(Widget* widget) {
    switch (widget->type) {
        case WIDGET_LABEL:
            renderLabel(widget);
            break;
        case WIDGET_ICON:
            renderIcon(widget);
            break;
        case WIDGET_PROGRESS_BAR:
            renderProgressBar(widget);
            break;
        case WIDGET_SCROLLABLE_TEXT:
            renderScrollableText(widget);
            break;
        default:
            break;
    }
}

void UIRenderer::renderLabel(Widget* widget) {
    Label* label = (Label*)widget->data;
    
    uint16_t x = widget->x;
    
    if (label->align == ALIGN_CENTER) {
        uint16_t textWidth = strlen(label->text) * 6 * label->fontSize;
        x = widget->x + (widget->width - textWidth) / 2;
    } else if (label->align == ALIGN_RIGHT) {
        uint16_t textWidth = strlen(label->text) * 6 * label->fontSize;
        x = widget->x + widget->width - textWidth;
    }
    
    // FIXED: Add color parameter
    display->drawText(x, widget->y, label->text, COLOR_WHITE, label->fontSize);
}

void UIRenderer::renderIcon(Widget* widget) {
    Icon* icon = (Icon*)widget->data;
    
    if (icon->bitmap) {
        // FIXED: Add color parameter
        display->drawBitmap(widget->x, widget->y, icon->bitmap, icon->width, icon->height, COLOR_WHITE);
    }
}

void UIRenderer::renderProgressBar(Widget* widget) {
    ProgressBar* bar = (ProgressBar*)widget->data;
    
    // FIXED: Add color parameter
    display->drawRect(widget->x, widget->y, widget->width, widget->height, COLOR_WHITE);
    
    uint16_t fillWidth = (bar->progress * (widget->width - 2)) / 100;
    // FIXED: Add color parameter
    display->fillRect(widget->x + 1, widget->y + 1, fillWidth, widget->height - 2, COLOR_WHITE);
    
    if (bar->showPercentage) {
        char text[8];
        snprintf(text, sizeof(text), "%d%%", bar->progress);
        
        uint16_t textX = widget->x + (widget->width - strlen(text) * 6) / 2;
        uint16_t textY = widget->y + 1;
        
        // FIXED: Add color parameter
        display->drawText(textX, textY, text, COLOR_WHITE, 1);
    }
}

void UIRenderer::renderScrollableText(Widget* widget) {
    ScrollableText* scrollText = (ScrollableText*)widget->data;
    
    if (scrollText->text) {
        // FIXED: Add color parameter
        display->drawText(widget->x - scrollText->scrollOffset, widget->y, scrollText->text, COLOR_WHITE, 1);
    }
}

int16_t UIRenderer::getWidgetIndex(int16_t id) {
    if (id < 0 || id >= widgetCount) {
        return -1;
    }
    
    return id;
}

void UIRenderer::fadeIn(uint16_t duration) {
    // Fade in animation (simplified)
    for (uint8_t i = 0; i < 10; i++) {
        render();
        delay(duration / 10);
    }
}

void UIRenderer::fadeOut(uint16_t duration) {
    // Fade out animation (simplified)
    for (uint8_t i = 10; i > 0; i--) {
        render();
        delay(duration / 10);
    }
    clear();
}

void UIRenderer::slideIn(uint16_t duration, bool fromLeft) {
    // Slide in animation (placeholder)
    render();
}
