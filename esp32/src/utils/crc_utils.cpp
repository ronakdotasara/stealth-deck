/**
 * ============================================================================
 * crc_utils.cpp - CRC16 Implementation
 * ============================================================================
 */

#include "crc_utils.h"

uint16_t crc16_ccitt(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    
    for (size_t i = 0; i < length; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        
        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc = crc << 1;
            }
        }
    }
    
    return crc;
}

uint16_t crc16_ccitt_continue(uint16_t crc, const uint8_t* data, size_t length) {
    for (size_t i = 0; i < length; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        
        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc = crc << 1;
            }
        }
    }
    
    return crc;
}

bool crc16_verify(const uint8_t* data, size_t length, uint16_t expected_crc) {
    uint16_t calculated_crc = crc16_ccitt(data, length);
    return calculated_crc == expected_crc;
}
