/**
 * ============================================================================
 * bluetooth_spp.cpp - Bluetooth Serial Port Profile Implementation
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-30
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * WARNING: ESP32-S3 does NOT support Classic Bluetooth (SPP)
 * This code is for ESP32 (non-S3) only.
 * For ESP32-S3, use BLE (Bluetooth Low Energy) instead.
 * ============================================================================
 */

#include "bluetooth_spp.h"
#include "../config.h"

// ============================================================================
// CONSTRUCTOR
// ============================================================================

BluetoothSPP::BluetoothSPP() :
    state(BT_STATE_IDLE),
    serverMode(false),
    clientMode(false),
    bytesReceived(0),
    bytesSent(0),
    lastActivityTime(0),
    dataCallback(nullptr),
    connectCallback(nullptr)
{
    strncpy(deviceName, BT_DEVICE_NAME, sizeof(deviceName) - 1);
    deviceName[sizeof(deviceName) - 1] = '\0';
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool BluetoothSPP::begin() {
    #ifdef CONFIG_BT_ENABLED
    if (!SerialBT.begin(deviceName)) {
        Serial.println("ERROR: Bluetooth initialization failed!");
        Serial.println("Note: ESP32-S3 doesn't support Classic Bluetooth");
        state = BT_STATE_ERROR;
        return false;
    }
    
    Serial.print("Bluetooth started: ");
    Serial.println(deviceName);
    state = BT_STATE_IDLE;
    return true;
    #else
    Serial.println("ERROR: Bluetooth not supported on this chip");
    Serial.println("ESP32-S3 only supports BLE, not Classic Bluetooth");
    state = BT_STATE_ERROR;
    return false;
    #endif
}

void BluetoothSPP::end() {
    #ifdef CONFIG_BT_ENABLED
    SerialBT.end();
    #endif
    state = BT_STATE_DISCONNECTED;
    Serial.println("Bluetooth stopped");
}

// ============================================================================
// SERVER/CLIENT MODE
// ============================================================================

bool BluetoothSPP::startServer() {
    if (state == BT_STATE_ERROR) {
        return false;
    }
    
    serverMode = true;
    clientMode = false;
    state = BT_STATE_IDLE;
    
    Serial.println("Bluetooth SPP server started");
    return true;
}

bool BluetoothSPP::startClient() {
    if (state == BT_STATE_ERROR) {
        return false;
    }
    
    serverMode = false;
    clientMode = true;
    state = BT_STATE_IDLE;
    
    Serial.println("Bluetooth SPP client started");
    return true;
}

// ============================================================================
// CONNECTION MANAGEMENT
// ============================================================================

bool BluetoothSPP::connect(const char* address) {
    #ifdef CONFIG_BT_ENABLED
    if (!clientMode) {
        Serial.println("ERROR: Not in client mode!");
        return false;
    }
    
    state = BT_STATE_CONNECTING;
    Serial.print("Connecting to: ");
    Serial.println(address);
    
    if (SerialBT.connect(address)) {
        state = BT_STATE_CONNECTED;
        if (connectCallback) {
            connectCallback(true);
        }
        Serial.println("✓ Connected!");
        return true;
    }
    
    state = BT_STATE_DISCONNECTED;
    if (connectCallback) {
        connectCallback(false);
    }
    Serial.println("✗ Connection failed!");
    return false;
    #else
    Serial.println("ERROR: Bluetooth not supported");
    return false;
    #endif
}

void BluetoothSPP::disconnect() {
    #ifdef CONFIG_BT_ENABLED
    SerialBT.disconnect();
    #endif
    
    state = BT_STATE_DISCONNECTED;
    
    if (connectCallback) {
        connectCallback(false);
    }
    
    Serial.println("Bluetooth disconnected");
}

bool BluetoothSPP::isConnected() {
    #ifdef CONFIG_BT_ENABLED
    return SerialBT.connected();
    #else
    return false;
    #endif
}

BTState BluetoothSPP::getState() {
    updateState();
    return state;
}

// ============================================================================
// DATA TRANSMISSION
// ============================================================================

size_t BluetoothSPP::send(const uint8_t* data, size_t length) {
    #ifdef CONFIG_BT_ENABLED
    if (!isConnected()) {
        return 0;
    }
    
    size_t sent = SerialBT.write(data, length);
    bytesSent += sent;
    lastActivityTime = millis();
    
    return sent;
    #else
    return 0;
    #endif
}

size_t BluetoothSPP::receive(uint8_t* buffer, size_t maxLength) {
    #ifdef CONFIG_BT_ENABLED
    if (!SerialBT.available()) {
        return 0;
    }
    
    size_t bytesRead = 0;
    while (SerialBT.available() && bytesRead < maxLength) {
        buffer[bytesRead++] = SerialBT.read();
    }
    
    bytesReceived += bytesRead;
    lastActivityTime = millis();
    
    if (dataCallback && bytesRead > 0) {
        dataCallback(buffer, bytesRead);
    }
    
    return bytesRead;
    #else
    return 0;
    #endif
}

size_t BluetoothSPP::available() {
    #ifdef CONFIG_BT_ENABLED
    return SerialBT.available();
    #else
    return 0;
    #endif
}

// ============================================================================
// DEVICE DISCOVERY
// ============================================================================

bool BluetoothSPP::discoverDevices(BTDevice* devices, uint8_t maxDevices, uint8_t& foundCount) {
    foundCount = 0;
    state = BT_STATE_DISCOVERING;
    
    Serial.println("Starting Bluetooth device discovery...");
    
    #ifdef CONFIG_BT_ENABLED
    // Note: ESP32 BluetoothSerial library doesn't have built-in discovery
    // You would need to use ESP32's native BLE scanning APIs instead
    Serial.println("WARNING: Device discovery not implemented");
    Serial.println("Use BLE scanning APIs for this functionality");
    #else
    Serial.println("ERROR: Bluetooth not supported on this chip");
    #endif
    
    state = BT_STATE_IDLE;
    return false;
}

// ============================================================================
// CONFIGURATION
// ============================================================================

void BluetoothSPP::setDeviceName(const char* name) {
    if (!name) return;
    
    strncpy(deviceName, name, sizeof(deviceName) - 1);
    deviceName[sizeof(deviceName) - 1] = '\0';
    
    Serial.printf("Bluetooth device name set to: %s\n", deviceName);
}

const char* BluetoothSPP::getDeviceName() {
    return deviceName;
}

// ============================================================================
// CALLBACKS
// ============================================================================

void BluetoothSPP::setDataCallback(std::function<void(const uint8_t*, size_t)> callback) {
    dataCallback = callback;
    Serial.println("Data callback registered");
}

void BluetoothSPP::setConnectCallback(std::function<void(bool)> callback) {
    connectCallback = callback;
    Serial.println("Connect callback registered");
}

// ============================================================================
// STATISTICS
// ============================================================================

uint32_t BluetoothSPP::getBytesReceived() {
    return bytesReceived;
}

uint32_t BluetoothSPP::getBytesSent() {
    return bytesSent;
}

// ============================================================================
// INTERNAL FUNCTIONS
// ============================================================================

void BluetoothSPP::handleIncomingData() {
    #ifdef CONFIG_BT_ENABLED
    if (available() > 0) {
        uint8_t buffer[BT_BUFFER_SIZE];
        size_t length = receive(buffer, BT_BUFFER_SIZE);
        
        if (length > 0 && dataCallback) {
            dataCallback(buffer, length);
        }
    }
    #endif
}

void BluetoothSPP::updateState() {
    bool connected = isConnected();
    
    if (connected && state != BT_STATE_CONNECTED) {
        state = BT_STATE_CONNECTED;
        Serial.println("Bluetooth connected");
        if (connectCallback) {
            connectCallback(true);
        }
    } else if (!connected && state == BT_STATE_CONNECTED) {
        state = BT_STATE_DISCONNECTED;
        Serial.println("Bluetooth disconnected");
        if (connectCallback) {
            connectCallback(false);
        }
    }
}

// ============================================================================
// END OF FILE
// ============================================================================
