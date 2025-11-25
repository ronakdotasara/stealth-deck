/**
 * ============================================================================
 * p2p_manager.cpp - P2P Manager Implementation
 * ============================================================================
 */

#include "p2p_manager.h"

P2PManager::P2PManager() {
    bluetooth = nullptr;
    state = P2P_STATE_IDLE;
    
    memset(&currentTransfer, 0, sizeof(currentTransfer));
    
    progressCallback = nullptr;
    completeCallback = nullptr;
    errorCallback = nullptr;
}

bool P2PManager::begin() {
    Serial.println("Initializing P2P Manager...");
    
    bluetooth = new BluetoothSPP();
    
    if (!bluetooth->begin()) {
        Serial.println("Bluetooth init failed");
        return false;
    }
    
    bluetooth->setDataCallback([this](const uint8_t* data, size_t length) {
        handleIncomingData();
    });
    
    bluetooth->setConnectCallback([this](bool connected) {
        if (connected) {
            state = P2P_STATE_CONNECTED;
            Serial.println("P2P connected");
        } else {
            state = P2P_STATE_IDLE;
            Serial.println("P2P disconnected");
        }
    });
    
    Serial.println("P2P Manager initialized");
    
    return true;
}

void P2PManager::update() {
    if (state == P2P_STATE_TRANSFERRING) {
        updateProgress();
    }
}

bool P2PManager::startDiscovery() {
    if (state != P2P_STATE_IDLE) {
        return false;
    }
    
    Serial.println("Starting device discovery...");
    
    state = P2P_STATE_DISCOVERING;
    
    BTDevice devices[10];
    uint8_t foundCount = 0;
    
    bluetooth->discoverDevices(devices, 10, foundCount);
    
    Serial.printf("Found %d devices\n", foundCount);
    
    for (uint8_t i = 0; i < foundCount; i++) {
        Serial.printf("Device: %s (%s) RSSI: %d\n", 
                     devices[i].name, 
                     devices[i].address, 
                     devices[i].rssi);
    }
    
    state = P2P_STATE_IDLE;
    
    return foundCount > 0;
}

bool P2PManager::connectToPeer(const char* address) {
    if (state != P2P_STATE_IDLE) {
        return false;
    }
    
    Serial.printf("Connecting to peer: %s\n", address);
    
    state = P2P_STATE_CONNECTING;
    
    if (bluetooth->connect(address)) {
        state = P2P_STATE_CONNECTED;
        return true;
    } else {
        state = P2P_STATE_ERROR;
        reportError("Connection failed");
        return false;
    }
}

void P2PManager::disconnect() {
    if (state == P2P_STATE_TRANSFERRING) {
        cancelTransfer();
    }
    
    bluetooth->disconnect();
    
    state = P2P_STATE_IDLE;
    
    Serial.println("P2P disconnected");
}

bool P2PManager::isConnected() {
    return state == P2P_STATE_CONNECTED || state == P2P_STATE_TRANSFERRING;
}

bool P2PManager::startSend(const char* filename, uint32_t size) {
    if (state != P2P_STATE_CONNECTED) {
        return false;
    }
    
    Serial.printf("Starting send: %s (%u bytes)\n", filename, size);
    
    strncpy(currentTransfer.filename, filename, MAX_FILENAME_LENGTH - 1);
    currentTransfer.fileSize = size;
    currentTransfer.bytesTransferred = 0;
    currentTransfer.progress = 0;
    currentTransfer.direction = TRANSFER_SEND;
    
    state = P2P_STATE_TRANSFERRING;
    
    return true;
}

bool P2PManager::startReceive() {
    if (state != P2P_STATE_CONNECTED) {
        return false;
    }
    
    Serial.println("Starting receive...");
    
    memset(&currentTransfer, 0, sizeof(currentTransfer));
    currentTransfer.direction = TRANSFER_RECEIVE;
    
    state = P2P_STATE_TRANSFERRING;
    
    return true;
}

void P2PManager::cancelTransfer() {
    if (state == P2P_STATE_TRANSFERRING) {
        Serial.println("Transfer cancelled");
        
        state = P2P_STATE_CONNECTED;
        
        if (completeCallback) {
            completeCallback(false);
        }
    }
}

P2PState P2PManager::getState() {
    return state;
}

P2PTransfer* P2PManager::getCurrentTransfer() {
    if (state == P2P_STATE_TRANSFERRING) {
        return &currentTransfer;
    }
    return nullptr;
}

uint8_t P2PManager::getProgress() {
    if (state == P2P_STATE_TRANSFERRING) {
        return currentTransfer.progress;
    }
    return 0;
}

void P2PManager::setProgressCallback(void (*callback)(uint8_t progress)) {
    progressCallback = callback;
}

void P2PManager::setCompleteCallback(void (*callback)(bool success)) {
    completeCallback = callback;
}

void P2PManager::setErrorCallback(void (*callback)(const char* error)) {
    errorCallback = callback;
}

void P2PManager::handleIncomingData() {
    if (state != P2P_STATE_TRANSFERRING) {
        return;
    }
    
    size_t available = bluetooth->available();
    
    if (available > 0) {
        uint8_t buffer[256];
        size_t received = bluetooth->receive(buffer, min((size_t)256, available));
        
        currentTransfer.bytesTransferred += received;
        
        updateProgress();
    }
}

void P2PManager::updateProgress() {
    if (currentTransfer.fileSize > 0) {
        uint8_t newProgress = (currentTransfer.bytesTransferred * 100) / currentTransfer.fileSize;
        
        if (newProgress != currentTransfer.progress) {
            currentTransfer.progress = newProgress;
            
            if (progressCallback) {
                progressCallback(newProgress);
            }
            
            Serial.printf("Transfer progress: %d%%\n", newProgress);
        }
        
        if (currentTransfer.bytesTransferred >= currentTransfer.fileSize) {
            Serial.println("Transfer complete");
            
            state = P2P_STATE_COMPLETE;
            
            if (completeCallback) {
                completeCallback(true);
            }
        }
    }
}

void P2PManager::reportError(const char* error) {
    Serial.printf("P2P Error: %s\n", error);
    
    if (errorCallback) {
        errorCallback(error);
    }
}
