#!/bin/bash
################################################################################
# install.sh - Installation Script for Stealth Deck Raspberry Pi
################################################################################
# Version: 1.0.0
# Date: 2025-11-24
# Author: Stealth Deck Project
# License: MIT
#
# Description:
#   Complete installation script for Stealth Deck on Raspberry Pi Zero 2W.
#   Installs system dependencies, Python packages, and configures the system.
#
# Usage:
#   sudo ./install.sh
#
# Requirements:
#   - Raspberry Pi OS (Bullseye or newer)
#   - Internet connection
#   - Sudo privileges
#
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

################################################################################
# CONFIGURATION
################################################################################

APP_NAME="Stealth Deck"
APP_DIR="/opt/stealth-deck"
VENV_DIR="${APP_DIR}/venv"
CONFIG_DIR="/etc/stealth-deck"
LOG_DIR="/var/log/stealth-deck"
DATA_DIR="/var/lib/stealth-deck"
SYSTEMD_DIR="/etc/systemd/system"

PYTHON_MIN_VERSION="3.9"
REQUIRED_RAM_MB=512

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# HELPER FUNCTIONS
################################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_system() {
    print_step "Checking system requirements..."
    
    # Check if running on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "This doesn't appear to be a Raspberry Pi"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_info "✓ Running on Raspberry Pi"
    fi
    
    # Check RAM
    total_ram=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$total_ram" -lt "$REQUIRED_RAM_MB" ]; then
        print_error "Insufficient RAM: ${total_ram}MB (minimum: ${REQUIRED_RAM_MB}MB)"
        exit 1
    fi
    print_info "✓ RAM: ${total_ram}MB"
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        python_version=$(python3 --version | awk '{print $2}')
        print_info "✓ Python: $python_version"
    else
        print_error "Python 3 not found"
        exit 1
    fi
    
    # Check disk space (need at least 1GB free)
    free_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$free_space" -lt 1048576 ]; then
        print_error "Insufficient disk space (need at least 1GB free)"
        exit 1
    fi
    print_info "✓ Disk space: $(($free_space / 1024))MB free"
    
    print_success "System requirements check passed"
}

################################################################################
# INSTALLATION STEPS
################################################################################

install_system_packages() {
    print_step "Installing system packages..."
    
    # Update package lists
    print_info "Updating package lists..."
    apt-get update -qq
    
    # Install essential build tools
    print_info "Installing build tools..."
    apt-get install -y -qq \
        build-essential \
        git \
        wget \
        curl \
        ca-certificates
    
    # Install Python dependencies
    print_info "Installing Python development packages..."
    apt-get install -y -qq \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        python3-venv
    
    # Install library dependencies
    print_info "Installing library dependencies..."
    apt-get install -y -qq \
        libatlas-base-dev \
        libjpeg-dev \
        zlib1g-dev \
        libopenblas-dev \
        liblapack-dev \
        gfortran \
        libbluetooth-dev \
        bluez \
        libportaudio2 \
        libcamera-dev \
        libcamera-apps \
        ffmpeg \
        libsm6 \
        libxext6 \
        libffi-dev \
        libssl-dev
    
    # Install Raspberry Pi specific packages
    print_info "Installing Raspberry Pi packages..."
    apt-get install -y -qq \
        raspberrypi-kernel-headers \
        python3-picamera2 \
        python3-gpiozero \
        python3-rpi.gpio
    
    print_success "System packages installed"
}

create_directories() {
    print_step "Creating directories..."
    
    # Create application directory
    mkdir -p "$APP_DIR"
    mkdir -p "$VENV_DIR"
    
    # Create configuration directory
    mkdir -p "$CONFIG_DIR"
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Create data directories
    mkdir -p "$DATA_DIR/notes"
    mkdir -p "$DATA_DIR/clipboard"
    mkdir -p "$DATA_DIR/cache"
    mkdir -p "$DATA_DIR/tmp"
    
    # Set permissions
    chmod 755 "$APP_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$LOG_DIR"
    chmod 700 "$DATA_DIR"  # Sensitive data
    
    print_success "Directories created"
}

create_virtual_environment() {
    print_step "Creating Python virtual environment..."
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    
    # Activate virtual environment
    source "${VENV_DIR}/bin/activate"
    
    # Upgrade pip, setuptools, wheel
    print_info "Upgrading pip, setuptools, wheel..."
    pip3 install --upgrade pip setuptools wheel
    
    print_success "Virtual environment created"
}

install_python_packages() {
    print_step "Installing Python packages..."
    
    # Activate virtual environment
    source "${VENV_DIR}/bin/activate"
    
    # Copy requirements.txt to temp location
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REQUIREMENTS_FILE="${SCRIPT_DIR}/../requirements.txt"
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "requirements.txt not found at: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    # Install packages one by one to avoid memory issues on Pi Zero
    print_info "Installing packages (this may take 10-20 minutes)..."
    
    # Install critical packages first
    pip3 install --no-cache-dir pyserial msgpack Pillow
    
    # Install remaining packages
    while IFS= read -r package; do
        # Skip comments and empty lines
        [[ "$package" =~ ^#.*$ ]] && continue
        [[ -z "$package" ]] && continue
        
        # Skip python-version line
        [[ "$package" =~ ^python-version ]] && continue
        
        print_info "Installing: $package"
        pip3 install --no-cache-dir --prefer-binary "$package" || {
            print_warning "Failed to install $package (non-critical)"
        }
    done < "$REQUIREMENTS_FILE"
    
    print_success "Python packages installed"
}

copy_application_files() {
    print_step "Copying application files..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
    
    # Copy source files
    print_info "Copying source files..."
    cp -r "${SCRIPT_DIR}/src" "${APP_DIR}/"
    cp -r "${SCRIPT_DIR}/data" "${APP_DIR}/"
    
    # Copy configuration template
    print_info "Copying configuration template..."
    cp "${SCRIPT_DIR}/config/config.json.template" "${CONFIG_DIR}/config.json"
    
    # Set permissions
    chmod -R 755 "${APP_DIR}/src"
    chmod 644 "${CONFIG_DIR}/config.json"
    
    print_success "Application files copied"
}

configure_uart() {
    print_step "Configuring UART..."
    
    # Enable UART in config.txt
    if ! grep -q "enable_uart=1" /boot/config.txt; then
        echo "enable_uart=1" >> /boot/config.txt
        print_info "UART enabled in /boot/config.txt"
    fi
    
    # Disable serial console
    if [ -f /boot/cmdline.txt ]; then
        sed -i 's/console=serial0,115200 //g' /boot/cmdline.txt
        sed -i 's/console=ttyAMA0,115200 //g' /boot/cmdline.txt
        print_info "Serial console disabled"
    fi
    
    # Add user to dialout group (for UART access)
    if [ -n "${SUDO_USER:-}" ]; then
        usermod -a -G dialout "$SUDO_USER"
        print_info "User $SUDO_USER added to dialout group"
    fi
    
    print_success "UART configured"
}

configure_bluetooth() {
    print_step "Configuring Bluetooth..."
    
    # Enable Bluetooth
    systemctl enable bluetooth
    systemctl start bluetooth
    
    # Add user to bluetooth group
    if [ -n "${SUDO_USER:-}" ]; then
        usermod -a -G bluetooth "$SUDO_USER"
        print_info "User $SUDO_USER added to bluetooth group"
    fi
    
    print_success "Bluetooth configured"
}

configure_camera() {
    print_step "Configuring camera..."
    
    # Enable camera in config.txt
    if ! grep -q "start_x=1" /boot/config.txt; then
        echo "start_x=1" >> /boot/config.txt
        print_info "Camera enabled in /boot/config.txt"
    fi
    
    # Set GPU memory
    if ! grep -q "gpu_mem=" /boot/config.txt; then
        echo "gpu_mem=128" >> /boot/config.txt
        print_info "GPU memory set to 128MB"
    fi
    
    # Add user to video group
    if [ -n "${SUDO_USER:-}" ]; then
        usermod -a -G video "$SUDO_USER"
        print_info "User $SUDO_USER added to video group"
    fi
    
    print_success "Camera configured"
}

install_systemd_service() {
    print_step "Installing systemd service..."
    
    # Create service file
    cat > "${SYSTEMD_DIR}/stealth-deck.service" <<EOF
[Unit]
Description=Stealth Deck AI Assistant Service
After=network.target bluetooth.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
ExecStart=${VENV_DIR}/bin/python3 ${APP_DIR}/src/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryLimit=400M
CPUQuota=80%

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable stealth-deck.service
    
    print_success "Systemd service installed"
}

configure_logging() {
    print_step "Configuring logging..."
    
    # Setup log rotation
    cat > /etc/logrotate.d/stealth-deck <<EOF
${LOG_DIR}/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
    
    print_success "Logging configured"
}

optimize_system() {
    print_step "Optimizing system..."
    
    # Reduce swap usage
    if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
        echo "vm.swappiness=10" >> /etc/sysctl.conf
        sysctl vm.swappiness=10
        print_info "Reduced swap usage"
    fi
    
    # Disable unnecessary services
    systemctl disable --now bluetooth-audio 2>/dev/null || true
    systemctl disable --now avahi-daemon 2>/dev/null || true
    
    print_success "System optimized"
}

################################################################################
# MAIN INSTALLATION
################################################################################

main() {
    clear
    print_header "Installing ${APP_NAME}"
    echo
    
    # Check prerequisites
    check_root
    check_system
    echo
    
    # Confirm installation
    print_warning "This will install ${APP_NAME} and modify system configuration."
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    echo
    
    # Run installation steps
    install_system_packages
    echo
    
    create_directories
    echo
    
    create_virtual_environment
    echo
    
    install_python_packages
    echo
    
    copy_application_files
    echo
    
    configure_uart
    echo
    
    configure_bluetooth
    echo
    
    configure_camera
    echo
    
    install_systemd_service
    echo
    
    configure_logging
    echo
    
    optimize_system
    echo
    
    # Final steps
    print_header "Installation Complete!"
    echo
    print_success "${APP_NAME} has been installed successfully!"
    echo
    print_info "Next steps:"
    echo "  1. Edit configuration: sudo nano ${CONFIG_DIR}/config.json"
    echo "  2. Add your Gemini API key to the config"
    echo "  3. Reboot the system: sudo reboot"
    echo "  4. Start the service: sudo systemctl start stealth-deck"
    echo "  5. Check status: sudo systemctl status stealth-deck"
    echo "  6. View logs: sudo journalctl -u stealth-deck -f"
    echo
    print_warning "A reboot is required for UART and camera changes to take effect."
    read -p "Reboot now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Rebooting in 5 seconds..."
        sleep 5
        reboot
    fi
}

# Run main function
main

################################################################################
# END OF FILE
################################################################################
