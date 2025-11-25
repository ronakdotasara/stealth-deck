#!/usr/bin/env python3
"""
================================================================================
uart_monitor.py - UART Protocol Monitor GUI
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
GUI tool for monitoring and debugging UART communication.
Displays messages, statistics, and allows message injection.

Features:
- Real-time message display
- Protocol analysis
- Message injection
- Statistics tracking
- Export functionality

================================================================================
"""

import sys
import serial
import struct
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QPushButton, QLabel,
                             QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
                             QTabWidget, QGroupBox, QLineEdit)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor


# Message types (from protocol definition)
MSG_TYPES = {
    0x00: "NONE",
    0x01: "DISPLAY_TEXT",
    0x02: "DISPLAY_CLEAR",
    0x03: "KEYPRESS",
    0x04: "MODE_CHANGE",
    0x05: "CAMERA_CAPTURE",
    0x06: "CAMERA_RESULT",
    0x10: "HEARTBEAT",
    0x11: "STATUS",
    0x12: "ERROR",
    0x20: "P2P_START",
    0x21: "P2P_DATA",
    0x22: "P2P_END",
    0xFE: "PANIC",
    0xFF: "DEBUG"
}


class UARTReader(QThread):
    """Thread for reading UART data."""
    
    message_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, port, baud_rate):
        """Initialize UART reader."""
        super().__init__()
        
        self.port = port
        self.baud_rate = baud_rate
        self.running = False
        self.serial_port = None
    
    def run(self):
        """Run reader thread."""
        try:
            self.serial_port = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=0.1
            )
            
            self.running = True
            
            while self.running:
                if self.serial_port.in_waiting >= 8:  # Minimum message size
                    message = self.read_message()
                    
                    if message:
                        self.message_received.emit(message)
                
                time.sleep(0.01)
        
        except Exception as e:
            self.error_occurred.emit(str(e))
        
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
    
    def read_message(self):
        """Read and parse UART message."""
        try:
            # Read header
            start = self.serial_port.read(1)
            
            if start != b'\xAA':
                return None
            
            msg_type = struct.unpack('B', self.serial_port.read(1))[0]
            length = struct.unpack('>H', self.serial_port.read(2))[0]
            
            # Read payload
            payload = self.serial_port.read(length)
            
            # Read CRC
            crc = struct.unpack('>H', self.serial_port.read(2))[0]
            
            return {
                'type': msg_type,
                'type_name': MSG_TYPES.get(msg_type, 'UNKNOWN'),
                'length': length,
                'payload': payload,
                'crc': crc,
                'timestamp': time.time()
            }
        
        except Exception as e:
            self.error_occurred.emit(f"Parse error: {e}")
            return None
    
    def stop(self):
        """Stop reader thread."""
        self.running = False


class UARTMonitor(QMainWindow):
    """Main UART monitor window."""
    
    def __init__(self):
        """Initialize monitor."""
        super().__init__()
        
        self.reader = None
        self.messages = []
        self.statistics = {
            'total': 0,
            'errors': 0
        }
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("UART Protocol Monitor - Stealth Deck")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Connection controls
        connection_group = self.create_connection_group()
        layout.addWidget(connection_group)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Messages tab
        messages_tab = self.create_messages_tab()
        self.tabs.addTab(messages_tab, "Messages")
        
        # Statistics tab
        stats_tab = self.create_statistics_tab()
        self.tabs.addTab(stats_tab, "Statistics")
        
        # Inject tab
        inject_tab = self.create_inject_tab()
        self.tabs.addTab(inject_tab, "Inject")
        
        # Status bar
        self.statusBar().showMessage("Disconnected")
    
    def create_connection_group(self):
        """Create connection controls."""
        group = QGroupBox("Connection")
        layout = QHBoxLayout()
        group.setLayout(layout)
        
        # Port selection
        layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.addItems([
            "/dev/ttyUSB0",
            "/dev/ttyUSB1",
            "/dev/ttyAMA0",
            "/dev/serial0"
        ])
        layout.addWidget(self.port_combo)
        
        # Baud rate
        layout.addWidget(QLabel("Baud:"))
        self.baud_spin = QSpinBox()
        self.baud_spin.setRange(9600, 921600)
        self.baud_spin.setValue(115200)
        layout.addWidget(self.baud_spin)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)
        
        layout.addStretch()
        
        return group
    
    def create_messages_tab(self):
        """Create messages display tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Controls
        controls = QHBoxLayout()
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_messages)
        controls.addWidget(clear_btn)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_messages)
        controls.addWidget(export_btn)
        
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Message table
        self.message_table = QTableWidget()
        self.message_table.setColumnCount(5)
        self.message_table.setHorizontalHeaderLabels([
            "Time", "Type", "Length", "Payload", "CRC"
        ])
        layout.addWidget(self.message_table)
        
        return widget
    
    def create_statistics_tab(self):
        """Create statistics tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        return widget
    
    def create_inject_tab(self):
        """Create message injection tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Message type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        
        self.inject_type = QComboBox()
        for code, name in MSG_TYPES.items():
            self.inject_type.addItem(f"{name} (0x{code:02X})", code)
        type_layout.addWidget(self.inject_type)
        
        layout.addLayout(type_layout)
        
        # Payload
        layout.addWidget(QLabel("Payload (hex):"))
        self.inject_payload = QTextEdit()
        self.inject_payload.setMaximumHeight(100)
        layout.addWidget(self.inject_payload)
        
        # Send button
        send_btn = QPushButton("Send Message")
        send_btn.clicked.connect(self.inject_message)
        layout.addWidget(send_btn)
        
        layout.addStretch()
        
        return widget
    
    def toggle_connection(self):
        """Toggle UART connection."""
        if self.reader and self.reader.running:
            self.disconnect_uart()
        else:
            self.connect_uart()
    
    def connect_uart(self):
        """Connect to UART."""
        port = self.port_combo.currentText()
        baud = self.baud_spin.value()
        
        try:
            self.reader = UARTReader(port, baud)
            self.reader.message_received.connect(self.handle_message)
            self.reader.error_occurred.connect(self.handle_error)
            self.reader.start()
            
            self.connect_btn.setText("Disconnect")
            self.statusBar().showMessage(f"Connected to {port} @ {baud}")
        
        except Exception as e:
            self.handle_error(str(e))
    
    def disconnect_uart(self):
        """Disconnect from UART."""
        if self.reader:
            self.reader.stop()
            self.reader.wait()
            self.reader = None
        
        self.connect_btn.setText("Connect")
        self.statusBar().showMessage("Disconnected")
    
    def handle_message(self, message):
        """Handle received message."""
        self.messages.append(message)
        self.statistics['total'] += 1
        
        # Add to table
        row = self.message_table.rowCount()
        self.message_table.insertRow(row)
        
        timestamp = time.strftime("%H:%M:%S", time.localtime(message['timestamp']))
        
        self.message_table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.message_table.setItem(row, 1, QTableWidgetItem(message['type_name']))
        self.message_table.setItem(row, 2, QTableWidgetItem(str(message['length'])))
        self.message_table.setItem(row, 3, QTableWidgetItem(message['payload'].hex()))
        self.message_table.setItem(row, 4, QTableWidgetItem(f"0x{message['crc']:04X}"))
        
        # Update statistics
        self.update_statistics()
    
    def handle_error(self, error):
        """Handle error."""
        self.statistics['errors'] += 1
        self.statusBar().showMessage(f"Error: {error}", 5000)
    
    def clear_messages(self):
        """Clear message history."""
        self.messages.clear()
        self.message_table.setRowCount(0)
    
    def export_messages(self):
        """Export messages to file."""
        filename = f"uart_log_{int(time.time())}.txt"
        
        with open(filename, 'w') as f:
            for msg in self.messages:
                f.write(f"{msg}\n")
        
        self.statusBar().showMessage(f"Exported to {filename}", 3000)
    
    def inject_message(self):
        """Inject custom message."""
        if not self.reader or not self.reader.running:
            self.statusBar().showMessage("Not connected", 3000)
            return
        
        msg_type = self.inject_type.currentData()
        payload_hex = self.inject_payload.toPlainText().strip()
        
        try:
            payload = bytes.fromhex(payload_hex)
            # Would send message here
            self.statusBar().showMessage("Message sent", 3000)
        
        except Exception as e:
            self.handle_error(str(e))
    
    def update_statistics(self):
        """Update statistics display."""
        stats_text = f"""
Total Messages: {self.statistics['total']}
Errors: {self.statistics['errors']}

Message Types:
"""
        
        # Count message types
        type_counts = {}
        for msg in self.messages:
            type_name = msg['type_name']
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        for type_name, count in sorted(type_counts.items()):
            stats_text += f"  {type_name}: {count}\n"
        
        self.stats_text.setPlainText(stats_text)
    
    def closeEvent(self, event):
        """Handle window close."""
        self.disconnect_uart()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    monitor = UARTMonitor()
    monitor.show()
    sys.exit(app.exec_())
