#!/bin/bash
################################################################################
# update.sh - Stealth Deck Update Script
################################################################################
# Version: 1.0.0
# Date: 2025-11-25
# Author: Stealth Deck Project
# License: MIT
#
# Description:
# Updates Stealth Deck software to the latest version.
# Handles git pull, dependency updates, and service restart.
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/stealth-deck"
SERVICE_NAME="stealth-deck"
BACKUP_DIR="/var/backups/stealth-deck"

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

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root (use sudo)"
        exit 1
    fi
}

backup_current() {
    log_info "Creating backup..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_path="$BACKUP_DIR/backup_$timestamp"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current installation
    cp -r "$INSTALL_DIR" "$backup_path"
    
    # Backup config
    if [ -f "/etc/stealth-deck/config.json" ]; then
        cp "/etc/stealth-deck/config.json" "$backup_path/config.json"
    fi
    
    log_info "Backup created: $backup_path"
}

update_code() {
    log_info "Updating code from repository..."
    
    cd "$INSTALL_DIR"
    
    # Check if git repository
    if [ -d ".git" ]; then
        # Stash local changes
        git stash
        
        # Pull latest changes
        git pull origin main
        
        log_info "Code updated successfully"
    else
        log_warn "Not a git repository, skipping git pull"
    fi
}

update_dependencies() {
    log_info "Updating Python dependencies..."
    
    cd "$INSTALL_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Update pip
    pip install --upgrade pip
    
    # Update dependencies
    pip install --upgrade -r requirements.txt
    
    deactivate
    
    log_info "Dependencies updated"
}

update_esp32_firmware() {
    log_info "Checking for ESP32 firmware updates..."
    
    if [ -d "$INSTALL_DIR/esp32" ]; then
        cd "$INSTALL_DIR/esp32"
        
        if command -v pio &> /dev/null; then
            log_info "Building ESP32 firmware..."
            pio run
            
            read -p "Flash firmware to ESP32? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                pio run -t upload
                log_info "Firmware flashed"
            fi
        else
            log_warn "PlatformIO not found, skipping firmware update"
        fi
    fi
}

restart_service() {
    log_info "Restarting service..."
    
    systemctl restart "$SERVICE_NAME"
    
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Service restarted successfully"
    else
        log_error "Service failed to start"
        log_info "Check logs: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
}

check_version() {
    log_info "Checking version..."
    
    if [ -f "$INSTALL_DIR/VERSION" ]; then
        version=$(cat "$INSTALL_DIR/VERSION")
        log_info "Current version: $version"
    else
        log_warn "Version file not found"
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    # Keep only last 5 backups
    if [ -d "$BACKUP_DIR" ]; then
        cd "$BACKUP_DIR"
        ls -t | tail -n +6 | xargs -r rm -rf
        log_info "Old backups cleaned"
    fi
}

main() {
    log_info "Starting Stealth Deck update..."
    
    check_root
    
    # Stop service
    log_info "Stopping service..."
    systemctl stop "$SERVICE_NAME"
    
    # Create backup
    backup_current
    
    # Update code
    update_code
    
    # Update dependencies
    update_dependencies
    
    # Update ESP32 firmware (optional)
    read -p "Update ESP32 firmware? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        update_esp32_firmware
    fi
    
    # Restart service
    restart_service
    
    # Check version
    check_version
    
    # Cleanup
    cleanup_old_backups
    
    log_info "Update complete!"
    log_info "Service status:"
    systemctl status "$SERVICE_NAME" --no-pager
}

# Run main function
main
