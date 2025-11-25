#!/bin/bash
################################################################################
# backup.sh - Stealth Deck Backup Script
################################################################################
# Version: 1.0.0
# Date: 2025-11-25
# Author: Stealth Deck Project
# License: MIT
#
# Description:
# Creates backup of Stealth Deck data, config, and notes.
# Supports local and remote backups.
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/stealth-deck"
CONFIG_DIR="/etc/stealth-deck"
DATA_DIR="/var/lib/stealth-deck"
BACKUP_DIR="/var/backups/stealth-deck"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="stealth-deck_$TIMESTAMP"

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

create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    
    backup_path="$BACKUP_DIR/$BACKUP_NAME"
    mkdir -p "$backup_path"
    
    echo "$backup_path"
}

backup_config() {
    local backup_path=$1
    
    log_info "Backing up configuration..."
    
    if [ -d "$CONFIG_DIR" ]; then
        cp -r "$CONFIG_DIR" "$backup_path/config"
        log_info "Config backed up"
    else
        log_warn "Config directory not found"
    fi
}

backup_data() {
    local backup_path=$1
    
    log_info "Backing up data..."
    
    if [ -d "$DATA_DIR" ]; then
        # Backup notes
        if [ -d "$DATA_DIR/notes" ]; then
            cp -r "$DATA_DIR/notes" "$backup_path/notes"
            log_info "Notes backed up"
        fi
        
        # Backup cache (optional)
        if [ -d "$DATA_DIR/cache" ]; then
            read -p "Backup cache? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp -r "$DATA_DIR/cache" "$backup_path/cache"
                log_info "Cache backed up"
            fi
        fi
        
        # Backup logs
        if [ -d "$DATA_DIR/logs" ]; then
            cp -r "$DATA_DIR/logs" "$backup_path/logs"
            log_info "Logs backed up"
        fi
    else
        log_warn "Data directory not found"
    fi
}

backup_code() {
    local backup_path=$1
    
    log_info "Backing up code..."
    
    if [ -d "$INSTALL_DIR" ]; then
        # Copy only essential files
        mkdir -p "$backup_path/code"
        
        # Python source
        if [ -d "$INSTALL_DIR/src" ]; then
            cp -r "$INSTALL_DIR/src" "$backup_path/code/"
        fi
        
        # Config files
        [ -f "$INSTALL_DIR/requirements.txt" ] && cp "$INSTALL_DIR/requirements.txt" "$backup_path/code/"
        [ -f "$INSTALL_DIR/VERSION" ] && cp "$INSTALL_DIR/VERSION" "$backup_path/code/"
        
        log_info "Code backed up"
    else
        log_warn "Installation directory not found"
    fi
}

create_archive() {
    local backup_path=$1
    
    log_info "Creating archive..."
    
    cd "$BACKUP_DIR"
    tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
    
    # Remove uncompressed backup
    rm -rf "$BACKUP_NAME"
    
    archive_size=$(du -h "$BACKUP_NAME.tar.gz" | cut -f1)
    log_info "Archive created: $BACKUP_NAME.tar.gz ($archive_size)"
}

encrypt_backup() {
    local archive="$BACKUP_DIR/$BACKUP_NAME.tar.gz"
    
    read -p "Encrypt backup? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Encrypting backup..."
        
        read -s -p "Enter encryption password: " password
        echo
        
        # Encrypt with openssl
        openssl enc -aes-256-cbc -salt -pbkdf2 -in "$archive" -out "$archive.enc" -k "$password"
        
        # Remove unencrypted archive
        rm "$archive"
        
        log_info "Backup encrypted: $BACKUP_NAME.tar.gz.enc"
    fi
}

upload_backup() {
    log_info "Upload backup to remote location? (y/n): "
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter remote path (e.g., user@host:/path): " remote_path
        
        if [ -n "$remote_path" ]; then
            log_info "Uploading backup..."
            
            if [ -f "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" ]; then
                scp "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" "$remote_path"
            elif [ -f "$BACKUP_DIR/$BACKUP_NAME.tar.gz" ]; then
                scp "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "$remote_path"
            fi
            
            log_info "Backup uploaded"
        fi
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t *.tar.gz* 2>/dev/null | tail -n +11 | xargs -r rm
    
    log_info "Old backups cleaned"
}

list_backups() {
    log_info "Available backups:"
    
    if [ -d "$BACKUP_DIR" ]; then
        cd "$BACKUP_DIR"
        ls -lh *.tar.gz* 2>/dev/null || log_warn "No backups found"
    else
        log_warn "Backup directory not found"
    fi
}

main() {
    log_info "Starting Stealth Deck backup..."
    
    check_root
    
    # Create backup directory
    backup_path=$(create_backup_dir)
    log_info "Backup path: $backup_path"
    
    # Backup components
    backup_config "$backup_path"
    backup_data "$backup_path"
    backup_code "$backup_path"
    
    # Create archive
    create_archive "$backup_path"
    
    # Optional encryption
    encrypt_backup
    
    # Optional upload
    upload_backup
    
    # Cleanup
    cleanup_old_backups
    
    log_info "Backup complete!"
    
    # List backups
    echo
    list_backups
}

# Run main function
main
