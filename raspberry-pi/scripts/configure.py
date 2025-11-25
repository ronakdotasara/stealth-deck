#!/usr/bin/env python3
"""
================================================================================
configure.py - Interactive Configuration Script
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

Description:
Interactive configuration wizard for Stealth Deck.
Guides user through setup process.
================================================================================
"""

import os
import sys
import json
import getpass
from pathlib import Path
from typing import Optional


class Colors:
    """Terminal colors."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.GREEN}[INFO]{Colors.END} {text}")


def print_warn(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}[ERROR]{Colors.END} {text}")


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default."""
    if default:
        user_input = input(f"{Colors.CYAN}{prompt} [{default}]:{Colors.END} ").strip()
        return user_input if user_input else default
    else:
        return input(f"{Colors.CYAN}{prompt}:{Colors.END} ").strip()


def get_password(prompt: str) -> str:
    """Get password input."""
    return getpass.getpass(f"{Colors.CYAN}{prompt}:{Colors.END} ")


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{Colors.CYAN}{prompt} [{default_str}]:{Colors.END} ").strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes']


def configure_api_keys() -> dict:
    """Configure API keys."""
    print_header("API Keys Configuration")
    
    config = {}
    
    print_info("Enter your Gemini API key")
    print("Get your key from: https://makersuite.google.com/app/apikey")
    
    gemini_key = get_input("Gemini API Key", "")
    
    if gemini_key:
        config['gemini_api_key'] = gemini_key
        print_info("Gemini API key saved")
    else:
        print_warn("No API key provided - AI features will not work")
    
    return config


def configure_hardware() -> dict:
    """Configure hardware settings."""
    print_header("Hardware Configuration")
    
    config = {}
    
    # UART settings
    print_info("UART Settings")
    config['uart_port'] = get_input("UART Port", "/dev/serial0")
    config['uart_baud'] = int(get_input("UART Baud Rate", "115200"))
    
    # Camera settings
    if get_yes_no("Enable camera?", True):
        config['camera_enabled'] = True
        config['camera_resolution'] = [1640, 1232]
        print_info("Camera enabled")
    else:
        config['camera_enabled'] = False
    
    # Display settings
    config['display_width'] = int(get_input("Display Width", "240"))
    config['display_height'] = int(get_input("Display Height", "536"))
    
    return config


def configure_ai() -> dict:
    """Configure AI settings."""
    print_header("AI Configuration")
    
    config = {}
    
    config['model'] = get_input("Gemini Model", "gemini-pro")
    config['vision_model'] = get_input("Vision Model", "gemini-pro-vision")
    
    temperature = get_input("Temperature (0.0-1.0)", "0.7")
    config['temperature'] = float(temperature)
    
    max_tokens = get_input("Max Tokens", "1024")
    config['max_tokens'] = int(max_tokens)
    
    config['cache_responses'] = get_yes_no("Cache responses?", True)
    
    return config


def configure_security() -> dict:
    """Configure security settings."""
    print_header("Security Configuration")
    
    config = {}
    
    config['encryption_enabled'] = get_yes_no("Enable encryption?", True)
    
    if config['encryption_enabled']:
        print_info("Encryption will be enabled")
    
    config['wipe_on_panic'] = get_yes_no("Wipe data on panic?", False)
    
    if config['wipe_on_panic']:
        print_warn("Data will be wiped on panic mode activation")
    
    # Set unlock code
    print_info("Set device unlock code (3 digits)")
    while True:
        code = get_password("Unlock code")
        
        if len(code) == 3 and code.isdigit():
            code_confirm = get_password("Confirm code")
            
            if code == code_confirm:
                config['unlock_code_hash'] = hash_unlock_code(code)
                print_info("Unlock code set")
                break
            else:
                print_error("Codes don't match")
        else:
            print_error("Code must be 3 digits")
    
    return config


def configure_storage() -> dict:
    """Configure storage settings."""
    print_header("Storage Configuration")
    
    config = {}
    
    cache_size = get_input("Max cache size (MB)", "100")
    config['max_cache_size_mb'] = int(cache_size)
    
    config['auto_cleanup'] = get_yes_no("Enable auto cleanup?", True)
    
    if config['auto_cleanup']:
        days = get_input("Cleanup after (days)", "30")
        config['cleanup_days'] = int(days)
    
    return config


def configure_power() -> dict:
    """Configure power settings."""
    print_header("Power Configuration")
    
    config = {}
    
    print("CPU Mode:")
    print("1. Power Save")
    print("2. Balanced")
    print("3. Performance")
    
    mode = get_input("Select mode", "2")
    
    modes = {
        "1": "powersave",
        "2": "balanced",
        "3": "performance"
    }
    
    config['cpu_mode'] = modes.get(mode, "balanced")
    
    config['auto_sleep'] = get_yes_no("Enable auto sleep?", True)
    
    if config['auto_sleep']:
        timeout = get_input("Sleep timeout (seconds)", "300")
        config['sleep_timeout'] = int(timeout)
    
    return config


def hash_unlock_code(code: str) -> str:
    """Hash unlock code."""
    import hashlib
    return hashlib.sha256(code.encode()).hexdigest()


def save_config(config: dict, config_file: str):
    """Save configuration to file."""
    try:
        # Create directory if needed
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print_info(f"Configuration saved: {config_file}")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to save config: {e}")
        return False


def main():
    """Main configuration wizard."""
    print_header("Stealth Deck Configuration Wizard")
    
    print("This wizard will guide you through the setup process.")
    print("Press Ctrl+C at any time to exit.\n")
    
    try:
        # Build configuration
        config = {
            'api_keys': configure_api_keys(),
            'hardware': configure_hardware(),
            'ai': configure_ai(),
            'security': configure_security(),
            'storage': configure_storage(),
            'power': configure_power()
        }
        
        # Show summary
        print_header("Configuration Summary")
        
        print(json.dumps(config, indent=2))
        print()
        
        # Confirm
        if get_yes_no("Save this configuration?", True):
            # Determine config file path
            if os.geteuid() == 0:
                config_file = "/etc/stealth-deck/config.json"
            else:
                config_file = os.path.expanduser("~/.config/stealth-deck/config.json")
            
            if save_config(config, config_file):
                print_header("Configuration Complete!")
                print_info("Configuration saved successfully")
                print_info("You can now start Stealth Deck")
                return 0
            else:
                print_error("Failed to save configuration")
                return 1
        else:
            print_warn("Configuration cancelled")
            return 1
    
    except KeyboardInterrupt:
        print("\n")
        print_warn("Configuration cancelled by user")
        return 1
    
    except Exception as e:
        print_error(f"Configuration failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
