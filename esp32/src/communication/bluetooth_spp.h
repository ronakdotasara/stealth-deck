/**
 * ============================================================================
 * bluetooth_spp.h - Bluetooth Serial Port Profile
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-24
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Bluetooth SPP (Serial Port Profile) for ESP32.
 * Enables wireless communication for P2P file transfers.
 * 
 * Features:
 * - SPP server/client modes
 * - Device discovery
 * - Pairing management
 * - Data transfer
 * - Connection monitoring
 * 
 * ============================================================================
 */

#ifndef BLUETOOTH_SPP_H
#define BLUETOOTH_SPP_H

#include <Arduino.h>
#include "BluetoothSerial.h"

#define BT_DEVICE_NAME "StealthDeck"
#define BT_PIN "1234"
#define BT_BUFFER_SIZE 1024

enum BTState {
    BT_STATE_IDLE,
    BT_STATE_DISCOVERING,
    BT_STATE_CONNECTING,
    BT_STATE_CONNECTED,
    BT_STATE_DISCONNECTED,
    BT_STATE_ERROR
};

struct BTDevice {
    char name[32];
    char address[18];
    int8_t rssi;
};

class BluetoothSPP {
public:
    BluetoothSPP();
    
    bool begin();
    void end();
    
    bool startServer();
    bool startClient();
    
    bool connect(const char* address);
    void disconnect();
    
    bool isConnected();
    BTState getState();
    
    size_t send(const uint8_t* data, size_t length);
    size_t receive(uint8_t* buffer, size_t maxLength);
    size_t available();
    
    bool discoverDevices(BTDevice* devices, uint8_t maxDevices, uint8_t& foundCount);
    
    void setDeviceName(const char* name);
    const char* getDeviceName();
    
    void setDataCallback(void (*callback)(const uint8_t* data, size_t length));
    void setConnectCallback(void (*callback)(bool connected));
    
    uint32_t getBytesReceived();
    uint32_t getBytesSent();
    
private:
    BluetoothSerial SerialBT;
    
    char deviceName[32];
    BTState state;
    
    bool serverMode;
    bool clientMode;
    
    uint32_t bytesReceived;
    uint32_t bytesSent;
    
    unsigned long lastActivityTime;
    
    void (*dataCallback)(const uint8_t*, size_t);
    void (*connectCallback)(bool);
    
    void handleIncomingData();
    void updateState();
};

#endif
