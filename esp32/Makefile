# Stealth Deck - ESP32 Makefile
# PlatformIO shortcuts

.PHONY: help build upload monitor clean test

# Default target
help:
	@echo "Stealth Deck - ESP32 Build System"
	@echo "===================================="
	@echo ""
	@echo "Available targets:"
	@echo "  make build     - Build firmware"
	@echo "  make upload    - Upload firmware to device"
	@echo "  make monitor   - Open serial monitor"
	@echo "  make clean     - Clean build files"
	@echo "  make test      - Run unit tests"
	@echo "  make size      - Show firmware size"
	@echo "  make erase     - Erase flash"
	@echo "  make menuconfig - Open ESP-IDF configuration"
	@echo ""

# Build commands
build:
	@echo "Building ESP32 firmware..."
	pio run

upload:
	@echo "Uploading firmware..."
	pio run -t upload

monitor:
	@echo "Opening serial monitor..."
	pio device monitor

upload-monitor: upload monitor

# Testing
test:
	@echo "Running tests..."
	pio test

test-verbose:
	@echo "Running tests (verbose)..."
	pio test -v

# Cleaning
clean:
	@echo "Cleaning build files..."
	pio run -t clean
	rm -rf .pio

clean-all: clean
	@echo "Removing all build artifacts..."
	rm -rf .pio*

# Utilities
size:
	@echo "Firmware size:"
	pio run -t size

erase:
	@echo "Erasing flash..."
	pio run -t erase

menuconfig:
	@echo "Opening menuconfig..."
	pio run -t menuconfig

# Device info
device-info:
	@echo "Device information:"
	pio device list

# Debugging
debug:
	@echo "Starting debugger..."
	pio debug

# OTA update
ota-upload:
	@echo "Uploading via OTA..."
	pio run -t upload -e esp32_ota

# Multiple environments
build-all:
	@echo "Building all environments..."
	pio run -e esp32
	pio run -e esp32_debug

# Code checking
check:
	@echo "Running static analysis..."
	pio check

# Dependencies
update-libs:
	@echo "Updating libraries..."
	pio pkg update

install-libs:
	@echo "Installing libraries..."
	pio pkg install

# Quick commands
dev: clean build upload monitor

release: clean build size
	@echo "Release build complete!"

all: clean build test size
	@echo "Complete build finished!"
