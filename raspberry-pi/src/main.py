#!/usr/bin/env python3
"""
================================================================================
main.py - Main Service Daemon for Stealth Deck Raspberry Pi
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Main entry point for the Stealth Deck Raspberry Pi application. This daemon:

- Manages all system components and their lifecycle
- Handles UART communication with ESP32
- Processes keypress events and routes to appropriate handlers
- Manages AI features (Gemini API, camera, search)
- Coordinates P2P transfers via Bluetooth
- Implements security features (panic mode, encryption)
- Monitors system health and resources
- Provides graceful shutdown and error recovery

================================================================================
ARCHITECTURE:

    ┌─────────────────────────────────────────────────────────┐
    │                     Main Service                        │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │          Configuration Manager                    │  │
    │  └───────────────────────────────────────────────────┘  │
    │  ┌───────────┬──────────┬──────────┬─────────────────┐  │
    │  │   UART    │  Camera  │ Gemini   │  Bluetooth     │  │
    │  │  Handler  │Controller│  Client  │  Manager       │  │
    │  └───────────┴──────────┴──────────┴─────────────────┘  │
    │  ┌───────────┬──────────┬──────────┬─────────────────┐  │
    │  │  Search   │Clipboard │  Notes   │  Security      │  │
    │  │  Engine   │ Manager  │ Manager  │  Manager       │  │
    │  └───────────┴──────────┴──────────┴─────────────────┘  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │          Power & State Manager                    │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
                            ↕ UART
                        ┌───────┐
                        │ ESP32 │
                        └───────┘

================================================================================
SYSTEM MODES:

MODE_CALCULATOR (0):    Stealth mode, no AI features active
MODE_SMART (1):         AI features unlocked, full functionality
MODE_P2P (2):           Peer-to-peer transfer active
MODE_WIFI_SNIFFER (3):  WiFi monitoring (handled by ESP32)
MODE_CLIPBOARD (4):     Clipboard history viewer
MODE_NOTES (5):         Encrypted notes manager
MODE_SETTINGS (6):      System configuration
MODE_PANIC (7):         Emergency lockdown mode

================================================================================
STARTUP SEQUENCE:

1. Load configuration from /etc/stealth-deck/config.json
2. Initialize logging system
3. Setup signal handlers (SIGTERM, SIGINT)
4. Initialize hardware interfaces (UART, camera, GPIO)
5. Initialize AI components (Gemini client)
6. Initialize feature modules (search, clipboard, notes)
7. Initialize security manager
8. Start main event loop
9. Send ready signal to ESP32

================================================================================
EVENT LOOP:

Main loop runs continuously at ~100Hz, processing:
- UART messages from ESP32
- Camera capture requests
- Gemini API responses (async)
- P2P transfer chunks
- Heartbeat monitoring
- Resource monitoring

================================================================================
GRACEFUL SHUTDOWN:

On SIGTERM/SIGINT:
1. Stop accepting new requests
2. Complete pending operations (max 5s timeout)
3. Close all file handles
4. Disconnect Bluetooth
5. Send shutdown notification to ESP32
6. Clean up temporary files
7. Exit with status code

================================================================================
ERROR HANDLING:

- Critical errors: Log, notify ESP32, attempt recovery
- Non-critical errors: Log, continue operation
- ESP32 communication loss: Retry with backoff, then reboot
- API failures: Cache and retry, fallback to offline mode
- Memory pressure: Clear caches, trigger garbage collection

================================================================================
RESOURCE LIMITS:

- Max memory: 400MB (80% of 512MB available)
- Max CPU: 80% sustained
- Disk cache: 100MB max
- API rate limits: Gemini 60 req/min
- Temperature: Throttle at 70°C

================================================================================
LOGGING:

- Level: INFO (production), DEBUG (development)
- Location: /var/log/stealth-deck/main.log
- Rotation: 10MB per file, keep 5 files
- Format: ISO timestamp + level + component + message

================================================================================
USAGE:

    # Start as daemon
    sudo systemctl start stealth-deck

    # Start manually (foreground)
    sudo python3 main.py

    # Start in debug mode
    sudo python3 main.py --debug

    # Stop daemon
    sudo systemctl stop stealth-deck

================================================================================
"""

import sys
import os
import signal
import time
import logging
import argparse
import traceback
from typing import Optional, Dict, Any
from pathlib import Path

# Add source directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Core modules
from src.core.config_manager import ConfigManager
from src.core.state_manager import StateManager
from src.core.power_manager import PowerManager
from src.core.security_manager import SecurityManager

# Communication modules
from src.communication.uart_handler import UARTHandler
from src.communication.bluetooth_manager import BluetoothManager

# Hardware modules
from src.hardware.camera_controller import CameraController
from src.hardware.battery_monitor import BatteryMonitor

# AI modules
from src.ai.gemini_client import GeminiClient
from src.ai.gemini_renderer import GeminiRenderer

# Feature modules
from src.features.search_engine import SearchEngine
from src.features.clipboard_manager import ClipboardManager
from src.features.notes_manager import NotesManager
from src.features.qr_generator import QRGenerator

# P2P modules
from src.p2p.p2p_manager import P2PManager

# Utilities
from src.utils.logger import setup_logger
from src.utils.memory_monitor import MemoryMonitor

# ============================================================================
# CONSTANTS
# ============================================================================

VERSION = "1.0.0"
APP_NAME = "Stealth Deck"
PID_FILE = "/var/run/stealth-deck.pid"
DEFAULT_CONFIG = "/etc/stealth-deck/config.json"

# System modes
MODE_CALCULATOR = 0
MODE_SMART = 1
MODE_P2P = 2
MODE_WIFI_SNIFFER = 3
MODE_CLIPBOARD = 4
MODE_NOTES = 5
MODE_SETTINGS = 6
MODE_PANIC = 7

# Exit codes
EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 1
EXIT_HARDWARE_ERROR = 2
EXIT_SIGNAL = 3
EXIT_EXCEPTION = 4

# ============================================================================
# GLOBAL STATE
# ============================================================================

# Shutdown flag
shutdown_requested = False

# Component instances
config: Optional[ConfigManager] = None
state: Optional[StateManager] = None
power: Optional[PowerManager] = None
security: Optional[SecurityManager] = None
uart: Optional[UARTHandler] = None
bluetooth: Optional[BluetoothManager] = None
camera: Optional[CameraController] = None
battery: Optional[BatteryMonitor] = None
gemini: Optional[GeminiClient] = None
renderer: Optional[GeminiRenderer] = None
search: Optional[SearchEngine] = None
clipboard: Optional[ClipboardManager] = None
notes: Optional[NotesManager] = None
qr: Optional[QRGenerator] = None
p2p: Optional[P2PManager] = None
memory_monitor: Optional[MemoryMonitor] = None

logger: Optional[logging.Logger] = None

# ============================================================================
# SIGNAL HANDLERS
# ============================================================================

def signal_handler(signum: int, frame) -> None:
    """
    Handle termination signals gracefully.
    
    Args:
        signum: Signal number (SIGTERM, SIGINT, etc.)
        frame: Current stack frame
    """
    global shutdown_requested
    
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name} ({signum})")
    
    if not shutdown_requested:
        shutdown_requested = True
        logger.info("Initiating graceful shutdown...")
    else:
        logger.warning("Forced shutdown - second signal received")
        sys.exit(EXIT_SIGNAL)


def sigusr1_handler(signum: int, frame) -> None:
    """
    Handle SIGUSR1 - Print status information.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("=== STATUS REPORT (SIGUSR1) ===")
    
    if state:
        logger.info(f"Current Mode: {state.current_mode}")
        logger.info(f"Device Unlocked: {state.device_unlocked}")
    
    if uart:
        logger.info(f"UART Connected: {uart.is_connected()}")
        stats = uart.get_stats()
        logger.info(f"UART Messages: {stats['messages_sent']} sent, "
                   f"{stats['messages_received']} received")
    
    if memory_monitor:
        mem_info = memory_monitor.get_memory_info()
        logger.info(f"Memory Usage: {mem_info['percent']:.1f}% "
                   f"({mem_info['used_mb']:.1f}/{mem_info['total_mb']:.1f} MB)")
    
    if power:
        logger.info(f"CPU Frequency: {power.get_cpu_frequency()} MHz")
        logger.info(f"CPU Temperature: {power.get_cpu_temperature():.1f}°C")
    
    logger.info("=" * 30)


# ============================================================================
# INITIALIZATION FUNCTIONS
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{VERSION} - AI Assistant Service"
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=DEFAULT_CONFIG,
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--no-daemon',
        action='store_true',
        help='Run in foreground (do not daemonize)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} v{VERSION}'
    )
    
    return parser.parse_args()


def initialize_logging(debug: bool = False) -> logging.Logger:
    """
    Initialize logging system.
    
    Args:
        debug: Enable debug level logging
        
    Returns:
        Logger instance
    """
    log_level = logging.DEBUG if debug else logging.INFO
    
    logger = setup_logger(
        name="stealth-deck",
        log_file="/var/log/stealth-deck/main.log",
        level=log_level,
        max_bytes=10 * 1024 * 1024,  # 10 MB
        backup_count=5
    )
    
    logger.info("=" * 70)
    logger.info(f"{APP_NAME} v{VERSION}")
    logger.info("=" * 70)
    
    return logger


def load_configuration(config_path: str) -> ConfigManager:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        ConfigManager instance
        
    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid
    """
    logger.info(f"Loading configuration from: {config_path}")
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    config = ConfigManager(config_path)
    
    logger.info("✓ Configuration loaded successfully")
    logger.debug(f"Hardware UART Port: {config.get('hardware.uart_port')}")
    logger.debug(f"Features Enabled: P2P={config.get('features.enable_p2p')}, "
                f"Search={config.get('features.enable_search')}")
    
    return config


def initialize_components() -> bool:
    """
    Initialize all system components.
    
    Returns:
        True if successful, False otherwise
    """
    global state, power, security, uart, bluetooth, camera, battery
    global gemini, renderer, search, clipboard, notes, qr, p2p, memory_monitor
    
    try:
        # ====================================================================
        # Core Components
        # ====================================================================
        logger.info("[1/14] Initializing state manager...")
        state = StateManager()
        state.set_mode(MODE_CALCULATOR)
        logger.info("  ✓ State manager initialized")
        
        logger.info("[2/14] Initializing power manager...")
        power = PowerManager()
        power.set_mode('idle')  # Start in low-power mode
        logger.info("  ✓ Power manager initialized")
        
        logger.info("[3/14] Initializing security manager...")
        security = SecurityManager(config)
        logger.info("  ✓ Security manager initialized")
        
        logger.info("[4/14] Initializing memory monitor...")
        memory_monitor = MemoryMonitor(threshold_percent=80.0)
        logger.info("  ✓ Memory monitor initialized")
        
        # ====================================================================
        # Communication
        # ====================================================================
        logger.info("[5/14] Initializing UART handler...")
        uart_port = config.get('hardware.uart_port', '/dev/serial0')
        uart_baud = config.get('hardware.uart_baud', 115200)
        uart = UARTHandler(uart_port, uart_baud)
        
        if not uart.connect():
            logger.error("  ✗ Failed to connect to UART")
            return False
        logger.info("  ✓ UART handler initialized")
        
        logger.info("[6/14] Initializing Bluetooth manager...")
        if config.get('features.enable_p2p', True):
            bluetooth = BluetoothManager()
            if not bluetooth.initialize():
                logger.warning("  ! Bluetooth initialization failed (non-critical)")
            else:
                logger.info("  ✓ Bluetooth manager initialized")
        else:
            logger.info("  - Bluetooth disabled in config")
        
        # ====================================================================
        # Hardware
        # ====================================================================
        logger.info("[7/14] Initializing camera controller...")
        camera_resolution = config.get('hardware.camera_resolution', [1640, 1232])
        camera = CameraController(resolution=camera_resolution)
        
        if not camera.initialize():
            logger.warning("  ! Camera initialization failed (non-critical)")
        else:
            logger.info("  ✓ Camera controller initialized")
        
        logger.info("[8/14] Initializing battery monitor...")
        battery = BatteryMonitor()
        logger.info("  ✓ Battery monitor initialized")
        
        # ====================================================================
        # AI Components
        # ====================================================================
        logger.info("[9/14] Initializing Gemini client...")
        api_key = config.get('api_keys.gemini_api_key')
        
        if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
            logger.error("  ✗ Gemini API key not configured!")
            logger.error("  Please set 'api_keys.gemini_api_key' in config.json")
            return False
        
        gemini = GeminiClient(api_key)
        logger.info("  ✓ Gemini client initialized")
        
        logger.info("[10/14] Initializing Gemini renderer...")
        renderer = GeminiRenderer(display_width=240)
        logger.info("  ✓ Gemini renderer initialized")
        
        # ====================================================================
        # Feature Modules
        # ====================================================================
        logger.info("[11/14] Initializing search engine...")
        if config.get('features.enable_search', True):
            search = SearchEngine()
            logger.info("  ✓ Search engine initialized")
        else:
            logger.info("  - Search disabled in config")
        
        logger.info("[12/14] Initializing clipboard manager...")
        clipboard = ClipboardManager(max_entries=10)
        logger.info("  ✓ Clipboard manager initialized")
        
        logger.info("[13/14] Initializing notes manager...")
        notes = NotesManager(
            notes_dir="/var/lib/stealth-deck/notes",
            encryption_key=security.get_encryption_key()
        )
        logger.info("  ✓ Notes manager initialized")
        
        logger.info("[14/14] Initializing QR generator...")
        qr = QRGenerator()
        logger.info("  ✓ QR generator initialized")
        
        # ====================================================================
        # P2P Manager (if enabled)
        # ====================================================================
        if config.get('features.enable_p2p', True) and bluetooth:
            logger.info("Initializing P2P manager...")
            p2p = P2PManager(bluetooth, gemini, camera)
            logger.info("  ✓ P2P manager initialized")
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ All components initialized successfully")
        logger.info("=" * 70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Component initialization failed: {e}")
        logger.debug(traceback.format_exc())
        return False


# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

def handle_keypress(key: int, event_type: int) -> None:
    """
    Handle keypress event from ESP32.
    
    Args:
        key: Key code
        event_type: Event type (press, release, long, etc.)
    """
    logger.debug(f"Keypress: key=0x{key:02X} type={event_type}")
    
    current_mode = state.current_mode
    
    # Route to appropriate handler based on current mode
    if current_mode == MODE_SMART:
        # In smart mode, handle AI queries
        if key == 0x12:  # OK key - trigger Gemini query
            handle_smart_query()
    
    elif current_mode == MODE_P2P:
        # P2P mode key handling
        if p2p:
            p2p.handle_key(key, event_type)
    
    elif current_mode == MODE_CLIPBOARD:
        # Clipboard navigation
        if key == 0x10:  # UP
            clipboard.scroll_up()
        elif key == 0x11:  # DOWN
            clipboard.scroll_down()
        elif key == 0x12:  # OK
            display_clipboard_entry()
    
    elif current_mode == MODE_NOTES:
        # Notes navigation
        if key == 0x10:  # UP
            notes.previous()
        elif key == 0x11:  # DOWN
            notes.next()
        elif key == 0x12:  # OK
            display_note()


def handle_camera_capture() -> None:
    """
    Handle camera capture request from ESP32.
    """
    logger.info("Camera capture requested")
    
    try:
        # Set power mode to active
        power.set_mode('active')
        
        # Capture image
        image_path = camera.capture()
        
        if not image_path:
            logger.error("Camera capture failed")
            uart.send_display_text("Camera error")
            return
        
        logger.info(f"Image captured: {image_path}")
        
        # Send to Gemini for analysis
        logger.info("Sending image to Gemini for analysis...")
        uart.send_display_text("Analyzing image...")
        
        prompt = "Analyze this image and provide a detailed description."
        response = gemini.analyze_image(image_path, prompt)
        
        if response:
            logger.info("Gemini response received")
            
            # Render response for display
            rendered = renderer.render(response)
            
            # Send to ESP32 for display
            uart.send_display_image(rendered)
            
            # Add to clipboard
            clipboard.add(response)
        else:
            logger.error("Gemini analysis failed")
            uart.send_display_text("Analysis failed")
        
    except Exception as e:
        logger.error(f"Camera capture error: {e}")
        logger.debug(traceback.format_exc())
        uart.send_display_text(f"Error: {str(e)}")
    
    finally:
        # Return to idle power mode
        power.set_mode('idle')


def handle_mode_change(new_mode: int) -> None:
    """
    Handle mode change request from ESP32.
    
    Args:
        new_mode: New mode to switch to
    """
    logger.info(f"Mode change requested: {state.current_mode} -> {new_mode}")
    
    # Update state
    state.set_mode(new_mode)
    
    # Mode-specific initialization
    if new_mode == MODE_P2P:
        if p2p:
            p2p.start()
    elif new_mode == MODE_SMART:
        uart.send_display_text("Smart mode active")
    elif new_mode == MODE_CLIPBOARD:
        display_clipboard()
    elif new_mode == MODE_NOTES:
        display_notes_list()


def handle_panic() -> None:
    """
    Handle panic signal from ESP32.
    Emergency lockdown procedure.
    """
    logger.warning("!!! PANIC MODE ACTIVATED !!!")
    
    try:
        # Execute panic procedures
        security.panic_mode()
        
        # Clear sensitive data
        if clipboard:
            clipboard.clear()
        
        # Close all connections
        if bluetooth:
            bluetooth.disconnect_all()
        
        # Stop P2P transfers
        if p2p:
            p2p.stop()
        
        # Clear Gemini cache
        if gemini:
            gemini.clear_cache()
        
        # Update state
        state.set_mode(MODE_PANIC)
        state.device_unlocked = False
        
        logger.info("Panic procedures completed")
        
    except Exception as e:
        logger.error(f"Panic procedure error: {e}")
        logger.debug(traceback.format_exc())


def handle_heartbeat() -> None:
    """
    Handle heartbeat from ESP32.
    """
    logger.debug("Heartbeat received from ESP32")
    
    # Send heartbeat response
    uart.send_heartbeat()


# ============================================================================
# FEATURE HANDLERS
# ============================================================================

def handle_smart_query() -> None:
    """
    Handle smart mode query (text input from T9).
    """
    # In a full implementation, this would:
    # 1. Get text input from T9 entry
    # 2. Send to Gemini
    # 3. Render and display response
    pass


def display_clipboard() -> None:
    """
    Display clipboard contents on screen.
    """
    if not clipboard:
        return
    
    entries = clipboard.get_all()
    
    if not entries:
        uart.send_display_text("Clipboard empty")
        return
    
    # Format clipboard list
    text = "=== CLIPBOARD ===\n\n"
    for i, entry in enumerate(entries, 1):
        preview = entry[:50] + "..." if len(entry) > 50 else entry
        text += f"{i}. {preview}\n"
    
    uart.send_display_text(text)


def display_clipboard_entry() -> None:
    """
    Display selected clipboard entry.
    """
    if not clipboard:
        return
    
    entry = clipboard.get_current()
    
    if entry:
        # Render full entry
        rendered = renderer.render(entry)
        uart.send_display_image(rendered)


def display_notes_list() -> None:
    """
    Display list of notes.
    """
    if not notes:
        return
    
    note_list = notes.list_notes()
    
    if not note_list:
        uart.send_display_text("No notes found")
        return
    
    text = "=== NOTES ===\n\n"
    for i, note in enumerate(note_list, 1):
        text += f"{i}. {note['title']}\n"
    
    uart.send_display_text(text)


def display_note() -> None:
    """
    Display selected note content.
    """
    if not notes:
        return
    
    note_content = notes.get_current()
    
    if note_content:
        rendered = renderer.render(note_content)
        uart.send_display_image(rendered)


# ============================================================================
# MAIN LOOP
# ============================================================================

def process_uart_messages() -> None:
    """
    Process pending UART messages from ESP32.
    """
    while uart.available():
        msg = uart.read_message()
        
        if not msg:
            continue
        
        msg_type = msg['type']
        payload = msg['payload']
        
        # Route message to appropriate handler
        if msg_type == 0x03:  # Keypress
            if len(payload) >= 2:
                handle_keypress(payload[0], payload[1])
        
        elif msg_type == 0x04:  # Camera capture
            handle_camera_capture()
        
        elif msg_type == 0x05:  # Mode change
            if len(payload) >= 1:
                handle_mode_change(payload[0])
        
        elif msg_type == 0x06:  # Panic
            handle_panic()
        
        elif msg_type == 0x07:  # Heartbeat
            handle_heartbeat()
        
        else:
            logger.warning(f"Unknown message type: 0x{msg_type:02X}")


def update_battery_status() -> None:
    """
    Update battery status and send to ESP32.
    """
    if not battery:
        return
    
    status = battery.get_status()
    
    uart.send_battery_status(
        percent=status['percent'],
        voltage=status['voltage'],
        charging=status['charging']
    )


def monitor_resources() -> None:
    """
    Monitor system resources and take action if needed.
    """
    if not memory_monitor:
        return
    
    # Check memory usage
    if memory_monitor.is_high():
        logger.warning("High memory usage detected")
        
        # Clear caches
        if gemini:
            gemini.clear_cache()
        
        if renderer:
            renderer.clear_cache()
        
        # Force garbage collection
        import gc
        gc.collect()
    
    # Check CPU temperature
    temp = power.get_cpu_temperature()
    if temp > 70.0:
        logger.warning(f"High CPU temperature: {temp:.1f}°C")
        power.throttle_cpu()


def main_loop() -> None:
    """
    Main event loop.
    """
    logger.info("Starting main event loop...")
    
    # Send ready signal to ESP32
    uart.send_heartbeat()
    
    loop_counter = 0
    last_heartbeat = time.time()
    last_battery_update = time.time()
    last_resource_check = time.time()
    
    while not shutdown_requested:
        try:
            loop_start = time.time()
            
            # Process UART messages
            process_uart_messages()
            
            # Send heartbeat every 5 seconds
            if time.time() - last_heartbeat >= 5.0:
                uart.send_heartbeat()
                last_heartbeat = time.time()
            
            # Update battery status every 60 seconds
            if time.time() - last_battery_update >= 60.0:
                update_battery_status()
                last_battery_update = time.time()
            
            # Monitor resources every 30 seconds
            if time.time() - last_resource_check >= 30.0:
                monitor_resources()
                last_resource_check = time.time()
            
            # Process P2P transfers
            if p2p and state.current_mode == MODE_P2P:
                p2p.process()
            
            loop_counter += 1
            
            # Sleep to maintain ~100Hz loop rate
            elapsed = time.time() - loop_start
            sleep_time = max(0.01 - elapsed, 0.001)
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            break
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.debug(traceback.format_exc())
            time.sleep(1)  # Prevent tight error loop
    
    logger.info(f"Main loop exited after {loop_counter} iterations")


# ============================================================================
# CLEANUP
# ============================================================================

def cleanup() -> None:
    """
    Clean up resources and shutdown gracefully.
    """
    logger.info("Starting cleanup...")
    
    try:
        # Stop P2P transfers
        if p2p:
            logger.info("  Stopping P2P manager...")
            p2p.stop()
        
        # Close camera
        if camera:
            logger.info("  Closing camera...")
            camera.close()
        
        # Disconnect Bluetooth
        if bluetooth:
            logger.info("  Disconnecting Bluetooth...")
            bluetooth.disconnect_all()
        
        # Close UART
        if uart:
            logger.info("  Closing UART...")
            uart.send_display_text("Shutting down...")
            uart.disconnect()
        
        # Clear security sensitive data
        if security:
            logger.info("  Clearing security data...")
            security.cleanup()
        
        # Remove PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            logger.info(f"  Removed PID file: {PID_FILE}")
        
        logger.info("✓ Cleanup complete")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        logger.debug(traceback.format_exc())


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    global logger, config
    
    # Parse arguments
    args = parse_arguments()
    
    # Initialize logging
    logger = initialize_logging(debug=args.debug)
    
    try:
        # Setup signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGUSR1, sigusr1_handler)
        logger.info("Signal handlers registered")
        
        # Load configuration
        config = load_configuration(args.config)
        
        # Initialize all components
        if not initialize_components():
            logger.error("Component initialization failed")
            return EXIT_HARDWARE_ERROR
        
        # Write PID file
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"PID file written: {PID_FILE}")
        
        # Start main loop
        main_loop()
        
        # Normal shutdown
        logger.info("Normal shutdown")
        return EXIT_SUCCESS
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return EXIT_CONFIG_ERROR
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        return EXIT_EXCEPTION
    
    finally:
        cleanup()


if __name__ == "__main__":
    sys.exit(main())

# ============================================================================
# END OF FILE
# ============================================================================
