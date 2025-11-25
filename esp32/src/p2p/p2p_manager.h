/**
 * ============================================================================
 * p2p_manager.h - ESP32 P2P Manager
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-25
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Manages peer-to-peer transfers on ESP32 side.
 * Coordinates with Bluetooth and UART for P2P operations.
 * 
 * Features:
 * - P2P connection management
 * - Transfer coordination
 * - Progress tracking
 * - Status reporting
 * 
 * ============================================================================
 */

#ifndef P2P_MANAGER_H
#define P2P_MANAGER_H

#include <Arduino.h>
#include "../communication/bluetooth_spp.h"

#define MAX_FILENAME_LENGTH 64

enum P2PState {
    P2P_STATE_IDLE,
    P2P_STATE_DISCOVERING,
    P2P_STATE_CONNECTING,
    P2P_STATE_CONNECTED,
    P2P_STATE_TRANSFERRING,
    P2P_STATE_COMPLETE,
    P2P_STATE_ERROR
};

enum TransferDirection {
    TRANSFER_SEND,
    TRANSFER_RECEIVE
};

struct P2PTransfer {
    char filename[MAX_FILENAME_LENGTH];
    uint32_t fileSize;
    uint32_t bytesTransferred;
    uint8_t progress;
    TransferDirection direction;
};

class P2PManager {
public:
    P2PManager();
    
    bool begin();
    void update();
    
    // Connection management
    bool startDiscovery();
    bool connectToPeer(const char* address);
    void disconnect();
    bool isConnected();
    
    // Transfer operations
    bool startSend(const char* filename, uint32_t size);
    bool startReceive();
    void cancelTransfer();
    
    // State queries
    P2PState getState();
    P2PTransfer* getCurrentTransfer();
    uint8_t getProgress();
    
    // Callbacks
    void setProgressCallback(void (*callback)(uint8_t progress));
    void setCompleteCallback(void (*callback)(bool success));
    void setErrorCallback(void (*callback)(const char* error));
    
private:
    BluetoothSPP* bluetooth;
    
    P2PState state;
    P2PTransfer currentTransfer;
    
    void (*progressCallback)(uint8_t);
    void (*completeCallback)(bool);
    void (*errorCallback)(const char*);
    
    void handleIncomingData();
    void updateProgress();
    void reportError(const char* error);
};

#endif
