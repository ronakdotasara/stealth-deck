/**
 * ============================================================================
 * crc_utils.h - CRC Utility Functions
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-30
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * CRC (Cyclic Redundancy Check) utility functions for data integrity checking.
 * ============================================================================
 */

#ifndef CRC_UTILS_H
#define CRC_UTILS_H

#include <Arduino.h>

/**
 * @brief Calculate CRC16-CCITT checksum
 * 
 * Polynomial: 0x1021
 * Initial value: 0xFFFF
 * Final XOR: 0x0000
 * 
 * @param data Pointer to data buffer
 * @param length Length of data in bytes
 * @return CRC16 checksum value
 */
uint16_t calculate_crc16(const uint8_t* data, size_t length);

/**
 * @brief Calculate CRC8 checksum
 * 
 * Polynomial: 0x07
 * Initial value: 0x00
 * 
 * @param data Pointer to data buffer
 * @param length Length of data in bytes
 * @return CRC8 checksum value
 */
uint8_t calculate_crc8(const uint8_t* data, size_t length);

/**
 * @brief Verify CRC16 checksum
 * 
 * @param data Pointer to data buffer
 * @param length Length of data in bytes
 * @param expected_crc Expected CRC value
 * @return true if CRC matches, false otherwise
 */
bool verify_crc16(const uint8_t* data, size_t length, uint16_t expected_crc);

/**
 * @brief Verify CRC8 checksum
 * 
 * @param data Pointer to data buffer
 * @param length Length of data in bytes
 * @param expected_crc Expected CRC value
 * @return true if CRC matches, false otherwise
 */
bool verify_crc8(const uint8_t* data, size_t length, uint8_t expected_crc);

#endif // CRC_UTILS_H
