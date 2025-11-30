/**
 * ============================================================================
 * @file encryption.h
 * @brief Encryption and Security Functions
 * @version 1.0.0
 * @date 2025-11-30
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Encryption utilities for secure P2P communication and data protection.
 * 
 * Features:
 * - AES-256 encryption/decryption
 * - Key generation and management
 * - Data hashing (SHA-256)
 * - Secure random number generation
 * 
 * ============================================================================
 */

#ifndef ENCRYPTION_H
#define ENCRYPTION_H

#include <Arduino.h>
#include "mbedtls/aes.h"
#include "mbedtls/sha256.h"
#include "mbedtls/md.h"

// ============================================================================
// CONSTANTS
// ============================================================================

#define AES_KEY_SIZE       32  // 256 bits
#define AES_BLOCK_SIZE     16  // 128 bits
#define SHA256_HASH_SIZE   32  // 256 bits
#define MAX_ENCRYPTED_SIZE 2048

// ============================================================================
// CLASS DEFINITION
// ============================================================================

class Encryption {
public:
    /**
     * @brief Constructor
     */
    Encryption();
    
    /**
     * @brief Destructor
     */
    ~Encryption();
    
    /**
     * @brief Initialize encryption system
     */
    void begin();
    
    /**
     * @brief Generate a random AES key
     * 
     * @param key Output buffer (must be AES_KEY_SIZE bytes)
     * @return true if successful
     */
    bool generateKey(uint8_t* key);
    
    /**
     * @brief Set encryption key
     * 
     * @param key Key buffer (AES_KEY_SIZE bytes)
     * @return true if successful
     */
    bool setKey(const uint8_t* key);
    
    /**
     * @brief Encrypt data using AES-256-CBC
     * 
     * @param plaintext Input data
     * @param length Input data length
     * @param ciphertext Output buffer
     * @param iv Initialization vector (16 bytes)
     * @return Encrypted data length, or 0 on error
     */
    size_t encrypt(const uint8_t* plaintext, size_t length,
                   uint8_t* ciphertext, uint8_t* iv);
    
    /**
     * @brief Decrypt data using AES-256-CBC
     * 
     * @param ciphertext Encrypted data
     * @param length Encrypted data length
     * @param plaintext Output buffer
     * @param iv Initialization vector (16 bytes)
     * @return Decrypted data length, or 0 on error
     */
    size_t decrypt(const uint8_t* ciphertext, size_t length,
                   uint8_t* plaintext, const uint8_t* iv);
    
    /**
     * @brief Calculate SHA-256 hash
     * 
     * @param data Input data
     * @param length Input data length
     * @param hash Output buffer (SHA256_HASH_SIZE bytes)
     * @return true if successful
     */
    bool sha256(const uint8_t* data, size_t length, uint8_t* hash);
    
    /**
     * @brief Calculate HMAC-SHA256
     * 
     * @param key HMAC key
     * @param keyLen Key length
     * @param data Input data
     * @param dataLen Input data length
     * @param hmac Output buffer (SHA256_HASH_SIZE bytes)
     * @return true if successful
     */
    bool hmacSha256(const uint8_t* key, size_t keyLen,
                    const uint8_t* data, size_t dataLen,
                    uint8_t* hmac);
    
    /**
     * @brief Generate random bytes
     * 
     * @param buffer Output buffer
     * @param length Number of bytes to generate
     */
    void randomBytes(uint8_t* buffer, size_t length);
    
    /**
     * @brief Simple XOR encryption (for demo/testing)
     * 
     * @param data Data to encrypt/decrypt
     * @param length Data length
     * @param key XOR key
     */
    void xorEncrypt(uint8_t* data, size_t length, uint8_t key);

private:
    mbedtls_aes_context _aesContext;
    uint8_t _key[AES_KEY_SIZE];
    bool _keySet;
    
    /**
     * @brief Add PKCS7 padding
     * 
     * @param data Data buffer
     * @param dataLen Original data length
     * @param paddedLen Output padded length
     * @return Padded data length
     */
    size_t addPadding(uint8_t* data, size_t dataLen, size_t* paddedLen);
    
    /**
     * @brief Remove PKCS7 padding
     * 
     * @param data Padded data
     * @param paddedLen Padded data length
     * @return Original data length
     */
    size_t removePadding(const uint8_t* data, size_t paddedLen);
};

#endif // ENCRYPTION_H
