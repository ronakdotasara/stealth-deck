#!/usr/bin/env python3
"""
================================================================================
esp32_simulator.py - ESP32 Hardware Simulator
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Simulates ESP32 hardware for testing without physical device.
Allows testing UART communication, display, and keypad.

Features:
- Virtual display
- Virtual keypad
- UART emulation
- State simulation
- Interactive GUI

================================================================================
"""

import sys
import threading
import time
from tkinter import Tk, Canvas, Frame, Button, Label, Text, Scrollbar
from tkinter import END, VERTICAL, RIGHT, LEFT, BOTH, Y
from queue import Queue


class VirtualDisplay:
    """Virtual OLED display."""
    
    def __init__(self, canvas, width=240, height=64):
        """Initialize virtual display."""
        self.canvas = canvas
        self.width = width
        self.height = height
        self.scale = 3  # Scale factor for visibility
        
        self.pixels = [[0 for _ in range(width)] for _ in range(height)]
        
        self.canvas.config(
            width=width * self.scale,
            height=height * self.scale,
            bg='black'
        )
    
    def clear(self):
        """Clear display."""
        self.pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.canvas.delete('all')
    
    def set_pixel(self, x, y, value):
        """Set pixel value."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = value
    
    def draw_text(self, x, y, text, size=1):
        """Draw text on display."""
        color = 'white'
        font_size = 8 * size
        
        self.canvas.create_text(
            x * self.scale,
            y * self.scale,
            text=text,
            fill=color,
            anchor='nw',
            font=('Courier', font_size)
        )
    
    def draw_rect(self, x, y, w, h, filled=False):
        """Draw rectangle."""
        if filled:
            self.canvas.create_rectangle(
                x * self.scale,
                y * self.scale,
                (x + w) * self.scale,
                (y + h) * self.scale,
                fill='white',
                outline='white'
            )
        else:
            self.canvas.create_rectangle(
                x * self.scale,
                y * self.scale,
                (x + w) * self.scale,
                (y + h) * self.scale,
                outline='white'
            )
    
    def update(self):
        """Update display."""
        self.canvas.update()


class VirtualKeypad:
    """Virtual 5x4 matrix keypad."""
    
    def __init__(self, parent, callback):
        """Initialize virtual keypad."""
        self.callback = callback
        
        self.keys = [
            ['7', '8', '9', '÷'],
            ['4', '5', '6', '×'],
            ['1', '2', '3', '-'],
            ['0', '.', '=', '+'],
            ['FN', 'DEL', 'MODE', 'OK']
        ]
        
        self.frame = Frame(parent)
        self.buttons = []
        
        for row_idx, row in enumerate(self.keys):
            button_row = []
            for col_idx, key in enumerate(row):
                btn = Button(
                    self.frame,
                    text=key,
                    width=4,
                    height=2,
                    command=lambda k=key: self.press_key(k)
                )
                btn.grid(row=row_idx, column=col_idx, padx=2, pady=2)
                button_row.append(btn)
            
            self.buttons.append(button_row)
    
    def press_key(self, key):
        """Handle key press."""
        if self.callback:
            self.callback(key)
    
    def get_frame(self):
        """Get keypad frame."""
        return self.frame


class VirtualUART:
    """Virtual UART interface."""
    
    def __init__(self):
        """Initialize virtual UART."""
        self.tx_queue = Queue()
        self.rx_queue = Queue()
        self.connected = False
    
    def send(self, data):
        """Send data."""
        self.tx_queue.put(data)
    
    def receive(self):
        """Receive data."""
        if not self.rx_queue.empty():
            return self.rx_queue.get()
        return None
    
    def available(self):
        """Check if data available."""
        return not self.rx_queue.empty()


class ESP32Simulator:
    """ESP32 hardware simulator."""
    
    def __init__(self):
        """Initialize simulator."""
        self.root = Tk()
        self.root.title("ESP32 Simulator - Stealth Deck")
        
        self.mode = 'calculator'
        self.display_text = []
        
        # Create UI
        self.setup_ui()
        
        # Virtual hardware
        self.display = VirtualDisplay(self.display_canvas)
        self.keypad = VirtualKeypad(self.keypad_frame, self.on_key_press)
        self.uart = VirtualUART()
        
        # State
        self.running = False
        self.update_thread = None
    
    def setup_ui(self):
        """Setup user interface."""
        # Main layout
        left_frame = Frame(self.root)
        left_frame.pack(side=LEFT, padx=10, pady=10)
        
        right_frame = Frame(self.root)
        right_frame.pack(side=RIGHT, padx=10, pady=10)
        
        # Display
        Label(left_frame, text="Display (240×64)").pack()
        self.display_canvas = Canvas(left_frame)
        self.display_canvas.pack()
        
        # Status
        self.status_label = Label(
            left_frame,
            text="Mode: Calculator | Status: Idle",
            font=('Arial', 10)
        )
        self.status_label.pack(pady=5)
        
        # Keypad
        Label(right_frame, text="Keypad").pack()
        self.keypad_frame = Frame(right_frame)
        self.keypad_frame.pack()
        
        # UART Log
        Label(right_frame, text="UART Log").pack(pady=(10, 0))
        
        log_frame = Frame(right_frame)
        log_frame.pack(fill=BOTH, expand=True)
        
        scrollbar = Scrollbar(log_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.uart_log = Text(
            log_frame,
            height=15,
            width=50,
            yscrollcommand=scrollbar.set,
            font=('Courier', 9)
        )
        self.uart_log.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.uart_log.yview)
        
        # Control buttons
        control_frame = Frame(right_frame)
        control_frame.pack(pady=10)
        
        Button(
            control_frame,
            text="Clear Log",
            command=self.clear_log
        ).pack(side=LEFT, padx=5)
        
        Button(
            control_frame,
            text="Reset",
            command=self.reset
        ).pack(side=LEFT, padx=5)
    
    def on_key_press(self, key):
        """Handle keypress."""
        self.log_uart(f"TX: Key pressed: {key}")
        
        # Simulate key handling
        if self.mode == 'calculator':
            self.handle_calculator_key(key)
        elif self.mode == 'smart':
            self.handle_smart_key(key)
        
        self.update_display()
    
    def handle_calculator_key(self, key):
        """Handle calculator mode key."""
        if key == 'MODE':
            self.mode = 'smart'
            self.display_text = ['Smart Mode']
            self.log_uart("Mode changed to Smart")
        
        elif key == 'FN':
            self.display_text = ['Function Menu']
        
        elif key == 'DEL':
            if self.display_text:
                self.display_text[-1] = self.display_text[-1][:-1]
        
        elif key == '=':
            # Simulate calculation
            if self.display_text:
                expr = self.display_text[-1]
                self.display_text.append(f"= {expr}")
        
        else:
            if not self.display_text:
                self.display_text = ['']
            self.display_text[-1] += key
    
    def handle_smart_key(self, key):
        """Handle smart mode key."""
        if key == 'MODE':
            self.mode = 'calculator'
            self.display_text = ['Calculator Mode']
            self.log_uart("Mode changed to Calculator")
        
        elif key == 'OK':
            self.display_text.append('Processing...')
            self.log_uart("Query sent to Raspberry Pi")
        
        else:
            if not self.display_text:
                self.display_text = ['']
            self.display_text[-1] += key
    
    def update_display(self):
        """Update virtual display."""
        self.display.clear()
        
        # Draw mode
        self.display.draw_text(0, 0, f"Mode: {self.mode.upper()}", 1)
        
        # Draw text lines
        y = 16
        for line in self.display_text[-4:]:  # Show last 4 lines
            self.display.draw_text(0, y, line[:30], 1)  # Max 30 chars
            y += 12
        
        self.display.update()
        
        # Update status
        self.status_label.config(
            text=f"Mode: {self.mode.capitalize()} | "
                 f"Lines: {len(self.display_text)}"
        )
    
    def log_uart(self, message):
        """Log UART message."""
        timestamp = time.strftime("%H:%M:%S")
        self.uart_log.insert(END, f"[{timestamp}] {message}\n")
        self.uart_log.see(END)
    
    def clear_log(self):
        """Clear UART log."""
        self.uart_log.delete(1.0, END)
    
    def reset(self):
        """Reset simulator."""
        self.mode = 'calculator'
        self.display_text = ['Ready']
        self.update_display()
        self.log_uart("System reset")
    
    def run(self):
        """Run simulator."""
        self.running = True
        self.display_text = ['Ready']
        self.update_display()
        self.log_uart("ESP32 Simulator started")
        
        self.root.mainloop()


def main():
    """Main function."""
    print("ESP32 Hardware Simulator")
    print("=" * 60)
    print("Simulating Stealth Deck ESP32...")
    print()
    
    simulator = ESP32Simulator()
    simulator.run()


if __name__ == '__main__':
    main()
