#!/bin/bash
################################################################################
# flash_esp32.sh - ESP32 Firmware Flashing Script
################################################################################
# Version: 1.0.0
# Date: 2025-11-25
# Author: Stealth Deck Project
# License: MIT
#
# Description:
# Flashes ESP32 firmware from Raspberry Pi.
# Handles compilation, upload, and verification.
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/stealth-deck"
ESP32_DIR="$INSTALL_DIR/esp32"
SERIAL_PORT="/dev/ttyUSB0"
BAUD_RATE="115200"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_dependencies() {
    log_step "Checking dependencies..."
    
    if ! command -v pio &> /dev/null; then
        log_error "PlatformIO not found"
        log_info "Install with: pip install platformio"
        exit 1
    fi
    
    log_info "Dependencies OK"
}

detect_esp32() {
    log_step "Detecting ESP32..."
    
    # Try common serial ports
    ports=("/dev/ttyUSB0" "/dev/ttyUSB1" "/dev/ttyACM0" "/dev/ttyACM1")
    
    for port in "${ports[@]}"; do
        if [ -e "$port" ]; then
            log_info "Found ESP32 on $port"
            SERIAL_PORT="$port"
            return 0
        fi
    done
    
    log_warn "ESP32 not detected automatically"
    read -p "Enter serial port (default: /dev/ttyUSB0): " user_port
    
    if [ -n "$user_port" ]; then
        SERIAL_PORT="$user_port"
    fi
    
    if [ ! -e "$SERIAL_PORT" ]; then
        log_error "Port $SERIAL_PORT not found"
        exit 1
    fi
}

build_firmware() {
    log_step "Building firmware..."
    
    cd "$ESP32_DIR"
    
    # Clean previous build
    pio run -t clean
    
    # Build firmware
    pio run
    
    if [ $? -eq 0 ]; then
        log_info "Build successful"
    else
        log_error "Build failed"
        exit 1
    fi
}

flash_firmware() {
    log_step "Flashing firmware..."
    
    cd "$ESP32_DIR"
    
    # Flash to ESP32
    pio run -t upload --upload-port "$SERIAL_PORT"
    
    if [ $? -eq 0 ]; then
        log_info "Flash successful"
    else
        log_error "Flash failed"
        exit 1
    fi
}

monitor_serial() {
    log_step "Opening serial monitor..."
    log_info "Press Ctrl+C to exit"
    
    cd "$ESP32_DIR"
    
    pio device monitor --port "$SERIAL_PORT" --baud "$BAUD_RATE"
}

erase_flash() {
    log_warn "This will erase all data on ESP32"
    read -p "Continue? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_step "Erasing flash..."
        
        cd "$ESP32_DIR"
        pio run -t erase
        
        log_info "Flash erased"
    fi
}

show_info() {
    log_step "ESP32 Information"
    
    cd "$ESP32_DIR"
    
    echo
    log_info "Board: ESP32 DevKit"
    log_info "Framework: Arduino"
    log_info "Upload Speed: 921600"
    log_info "Monitor Speed: $BAUD_RATE"
    log_info "Port: $SERIAL_PORT"
    echo
}

interactive_menu() {
    while true; do
        echo
        echo "========================================="
        echo "  Stealth Deck ESP32 Flash Tool"
        echo "========================================="
        echo "1. Build firmware"
        echo "2. Flash firmware"
        echo "3. Build and flash"
        echo "4. Serial monitor"
        echo "5. Erase flash"
        echo "6. Show info"
        echo "0. Exit"
        echo "========================================="
        read -p "Select option: " choice
        
        case $choice in
            1)
                build_firmware
                ;;
            2)
                detect_esp32
                flash_firmware
                ;;
            3)
                detect_esp32
                build_firmware
                flash_firmware
                ;;
            4)
                detect_esp32
                monitor_serial
                ;;
            5)
                detect_esp32
                erase_flash
                ;;
            6)
                show_info
                ;;
            0)
                log_info "Exiting..."
                exit 0
                ;;
            *)
                log_error "Invalid option"
                ;;
        esac
    done
}

main() {
    log_info "ESP32 Flash Tool"
    
    check_dependencies
    
    # Check if ESP32 directory exists
    if [ ! -d "$ESP32_DIR" ]; then
        log_error "ESP32 directory not found: $ESP32_DIR"
        exit 1
    fi
    
    # Check for command line arguments
    if [ $# -eq 0 ]; then
        # Interactive mode
        interactive_menu
    else
        # Command line mode
        case "$1" in
            build)
                build_firmware
                ;;
            flash)
                detect_esp32
                flash_firmware
                ;;
            all)
                detect_esp32
                build_firmware
                flash_firmware
                ;;
            monitor)
                detect_esp32
                monitor_serial
                ;;
            erase)
                detect_esp32
                erase_flash
                ;;
            info)
                show_info
                ;;
            *)
                echo "Usage: $0 [build|flash|all|monitor|erase|info]"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"
