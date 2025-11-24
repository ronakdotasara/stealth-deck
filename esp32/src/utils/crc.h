/**
 * ============================================================================
 * crc.h - CRC Calculation Utilities
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-24
 * 
 * ============================================================================
 * DESCRIPTION:
 * CRC16 and CRC32 calculation utilities for data integrity.
 * 
 * ============================================================================
 */

#ifndef CRC_H
#define CRC_H

#include <Arduino.h>

class CRC {
public:
    static uint16_t crc16_ccitt(const uint8_t* data, size_t length);
    static uint16_t crc16_ccitt_update(uint16_t crc, uint8_t data);
    
    static uint32_t crc32(const uint8_t* data, size_t length);
    static uint32_t crc32_update(uint32_t crc, uint8_t data);
    
    static bool verify_crc16(const uint8_t* data, size_t length, uint16_t expected);
    static bool verify_crc32(const uint8_t* data, size_t length, uint32_t expected);

private:
    static const uint16_t CRC16_CCITT_TABLE[256];
    static const uint32_t CRC32_TABLE[256];
};

#endif
