/**
 * ============================================================================
 * wifi_sniffer.h - WiFi Packet Sniffer for ESP32
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-24
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * WiFi packet sniffer and network analyzer for ESP32.
 * Monitors WiFi networks, channels, and signal strength.
 * 
 * Features:
 * - WiFi network scanning
 * - Signal strength monitoring (RSSI)
 * - Channel analysis
 * - Encryption type detection
 * - Packet statistics
 * - Promiscuous mode (optional)
 * 
 * ============================================================================
 */

#ifndef WIFI_SNIFFER_H
#define WIFI_SNIFFER_H

#include <Arduino.h>
#include <WiFi.h>

#define MAX_NETWORKS 50
#define MAX_CHANNEL 14

enum WiFiSecurityType {
    WIFI_OPEN,
    WIFI_WEP,
    WIFI_WPA,
    WIFI_WPA2,
    WIFI_WPA3,
    WIFI_ENTERPRISE
};

struct WiFiNetwork {
    char ssid[33];
    uint8_t bssid[6];
    int8_t rssi;
    uint8_t channel;
    WiFiSecurityType security;
    bool hidden;
};

struct ChannelStats {
    uint8_t channel;
    uint16_t networkCount;
    int8_t avgRSSI;
    uint16_t packetCount;
};

class WiFiSniffer {
public:
    WiFiSniffer();
    
    bool begin();
    void end();
    
    uint16_t scanNetworks();
    WiFiNetwork* getNetwork(uint16_t index);
    uint16_t getNetworkCount();
    
    void startChannelHopping();
    void stopChannelHopping();
    void setChannel(uint8_t channel);
    uint8_t getCurrentChannel();
    
    ChannelStats* getChannelStats(uint8_t channel);
    void analyzeChannels();
    
    void startPromiscuousMode();
    void stopPromiscuousMode();
    bool isPromiscuousModeActive();
    
    uint32_t getPacketCount();
    void resetStatistics();
    
    void sortNetworksByRSSI();
    void sortNetworksByChannel();
    
    const char* getSecurityName(WiFiSecurityType type);
    
private:
    WiFiNetwork networks[MAX_NETWORKS];
    uint16_t networkCount;
    
    ChannelStats channelStats[MAX_CHANNEL + 1];
    
    uint8_t currentChannel;
    bool channelHopping;
    unsigned long lastChannelSwitch;
    uint16_t hopInterval;
    
    bool promiscuousMode;
    uint32_t packetCount;
    
    void updateChannelStats();
    void clearNetworks();
    
    static void promiscuousCallback(void* buf, wifi_promiscuous_pkt_type_t type);
    static WiFiSniffer* instance;
};

#endif
