/**
 * ============================================================================
 * wifi_sniffer.cpp - WiFi Sniffer Implementation
 * ============================================================================
 */

#include "wifi_sniffer.h"
#include "esp_wifi.h"

WiFiSniffer* WiFiSniffer::instance = nullptr;

WiFiSniffer::WiFiSniffer() {
    networkCount = 0;
    currentChannel = 1;
    channelHopping = false;
    lastChannelSwitch = 0;
    hopInterval = 500;
    promiscuousMode = false;
    packetCount = 0;
    
    instance = this;
    
    memset(networks, 0, sizeof(networks));
    memset(channelStats, 0, sizeof(channelStats));
}

bool WiFiSniffer::begin() {
    Serial.println("Initializing WiFi Sniffer...");
    
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    
    delay(100);
    
    Serial.println("WiFi Sniffer initialized");
    return true;
}

void WiFiSniffer::end() {
    stopPromiscuousMode();
    stopChannelHopping();
    
    WiFi.mode(WIFI_OFF);
}

uint16_t WiFiSniffer::scanNetworks() {
    Serial.println("Scanning WiFi networks...");
    
    clearNetworks();
    
    int n = WiFi.scanNetworks(false, true, false, 300);
    
    if (n == -1) {
        Serial.println("Scan failed");
        return 0;
    }
    
    Serial.print("Found ");
    Serial.print(n);
    Serial.println(" networks");
    
    for (int i = 0; i < n && networkCount < MAX_NETWORKS; i++) {
        strncpy(networks[networkCount].ssid, WiFi.SSID(i).c_str(), 32);
        networks[networkCount].ssid[32] = '\0';
        
        uint8_t* bssid = WiFi.BSSID(i);
        memcpy(networks[networkCount].bssid, bssid, 6);
        
        networks[networkCount].rssi = WiFi.RSSI(i);
        networks[networkCount].channel = WiFi.channel(i);
        
        wifi_auth_mode_t authMode = (wifi_auth_mode_t)WiFi.encryptionType(i);
        
        switch (authMode) {
            case WIFI_AUTH_OPEN:
                networks[networkCount].security = WIFI_OPEN;
                break;
            case WIFI_AUTH_WEP:
                networks[networkCount].security = WIFI_WEP;
                break;
            case WIFI_AUTH_WPA_PSK:
                networks[networkCount].security = WIFI_WPA;
                break;
            case WIFI_AUTH_WPA2_PSK:
                networks[networkCount].security = WIFI_WPA2;
                break;
            case WIFI_AUTH_WPA3_PSK:
                networks[networkCount].security = WIFI_WPA3;
                break;
            default:
                networks[networkCount].security = WIFI_WPA2;
                break;
        }
        
        networks[networkCount].hidden = (strlen(networks[networkCount].ssid) == 0);
        
        networkCount++;
    }
    
    WiFi.scanDelete();
    
    updateChannelStats();
    
    return networkCount;
}

WiFiNetwork* WiFiSniffer::getNetwork(uint16_t index) {
    if (index < networkCount) {
        return &networks[index];
    }
    return nullptr;
}

uint16_t WiFiSniffer::getNetworkCount() {
    return networkCount;
}

void WiFiSniffer::startChannelHopping() {
    Serial.println("Starting channel hopping...");
    
    channelHopping = true;
    currentChannel = 1;
    lastChannelSwitch = millis();
}

void WiFiSniffer::stopChannelHopping() {
    channelHopping = false;
}

void WiFiSniffer::setChannel(uint8_t channel) {
    if (channel < 1 || channel > MAX_CHANNEL) {
        return;
    }
    
    currentChannel = channel;
    esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
}

uint8_t WiFiSniffer::getCurrentChannel() {
    return currentChannel;
}

ChannelStats* WiFiSniffer::getChannelStats(uint8_t channel) {
    if (channel >= 1 && channel <= MAX_CHANNEL) {
        return &channelStats[channel];
    }
    return nullptr;
}

void WiFiSniffer::analyzeChannels() {
    memset(channelStats, 0, sizeof(channelStats));
    
    for (uint16_t i = 0; i < networkCount; i++) {
        uint8_t ch = networks[i].channel;
        
        if (ch >= 1 && ch <= MAX_CHANNEL) {
            channelStats[ch].channel = ch;
            channelStats[ch].networkCount++;
            channelStats[ch].avgRSSI += networks[i].rssi;
        }
    }
    
    for (uint8_t ch = 1; ch <= MAX_CHANNEL; ch++) {
        if (channelStats[ch].networkCount > 0) {
            channelStats[ch].avgRSSI /= channelStats[ch].networkCount;
        }
    }
}

void WiFiSniffer::startPromiscuousMode() {
    if (promiscuousMode) {
        return;
    }
    
    Serial.println("Starting promiscuous mode...");
    
    WiFi.disconnect();
    
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_rx_cb(&WiFiSniffer::promiscuousCallback);
    
    promiscuousMode = true;
    
    Serial.println("Promiscuous mode active");
}

void WiFiSniffer::stopPromiscuousMode() {
    if (!promiscuousMode) {
        return;
    }
    
    Serial.println("Stopping promiscuous mode...");
    
    esp_wifi_set_promiscuous(false);
    
    promiscuousMode = false;
}

bool WiFiSniffer::isPromiscuousModeActive() {
    return promiscuousMode;
}

uint32_t WiFiSniffer::getPacketCount() {
    return packetCount;
}

void WiFiSniffer::resetStatistics() {
    packetCount = 0;
    memset(channelStats, 0, sizeof(channelStats));
}

void WiFiSniffer::sortNetworksByRSSI() {
    for (uint16_t i = 0; i < networkCount - 1; i++) {
        for (uint16_t j = i + 1; j < networkCount; j++) {
            if (networks[j].rssi > networks[i].rssi) {
                WiFiNetwork temp = networks[i];
                networks[i] = networks[j];
                networks[j] = temp;
            }
        }
    }
}

void WiFiSniffer::sortNetworksByChannel() {
    for (uint16_t i = 0; i < networkCount - 1; i++) {
        for (uint16_t j = i + 1; j < networkCount; j++) {
            if (networks[j].channel < networks[i].channel) {
                WiFiNetwork temp = networks[i];
                networks[i] = networks[j];
                networks[j] = temp;
            }
        }
    }
}

const char* WiFiSniffer::getSecurityName(WiFiSecurityType type) {
    switch (type) {
        case WIFI_OPEN: return "Open";
        case WIFI_WEP: return "WEP";
        case WIFI_WPA: return "WPA";
        case WIFI_WPA2: return "WPA2";
        case WIFI_WPA3: return "WPA3";
        case WIFI_ENTERPRISE: return "Enterprise";
        default: return "Unknown";
    }
}

void WiFiSniffer::updateChannelStats() {
    analyzeChannels();
}

void WiFiSniffer::clearNetworks() {
    networkCount = 0;
    memset(networks, 0, sizeof(networks));
}

void WiFiSniffer::promiscuousCallback(void* buf, wifi_promiscuous_pkt_type_t type) {
    if (instance) {
        instance->packetCount++;
        
        if (instance->channelHopping) {
            unsigned long currentTime = millis();
            
            if (currentTime - instance->lastChannelSwitch > instance->hopInterval) {
                instance->currentChannel++;
                
                if (instance->currentChannel > MAX_CHANNEL) {
                    instance->currentChannel = 1;
                }
                
                instance->setChannel(instance->currentChannel);
                instance->lastChannelSwitch = currentTime;
            }
        }
    }
}
