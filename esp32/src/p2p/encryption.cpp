/**
 * ============================================================================
 * encryption.cpp - Encryption Implementation
 * ============================================================================
 */

#include "encryption.h"
#include "esp_random.h"

// ============================================================================
// CONSTRUCTOR & DESTRUCTOR
// ============================================================================

Encryption::Encryption() : _keySet(false) {
    memset(_key, 0, AES_KEY_SIZE);
}

Encryption::~Encryption() {
    mbedtls_aes_free(&_aesContext);
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void Encryption::begin() {
    mbedtls_aes_init(&_aesContext);
    Serial.println("│ ✓ Encryption ready (AES-256)");
}

// ============================================================================
// KEY MANAGEMENT
// ============================================================================

bool Encryption::generateKey(uint8_t* key) {
    if (!key) return false;
    
    randomBytes(key, AES_KEY_SIZE);
    
    Serial.println("Generated new encryption key");
    return true;
}

bool Encryption::setKey(const uint8_t* key) {
    if (!key) return false;
    
    memcpy(_key, key, AES_KEY_SIZE);
    _keySet = true;
    
    // Set encryption key
    int ret = mbedtls_aes_setkey_enc(&_aesContext, _key, AES_KEY_SIZE * 8);
    if (ret != 0) {
        Serial.printf("ERROR: Failed to set encryption key (%d)\n", ret);
        return false;
    }
    
    // Set decryption key
    ret = mbedtls_aes_setkey_dec(&_aesContext, _key, AES_KEY_SIZE * 8);
    if (ret != 0) {
        Serial.printf("ERROR: Failed to set decryption key (%d)\n", ret);
        return false;
    }
    
    Serial.println("Encryption key set");
    return true;
}

// ============================================================================
// ENCRYPTION / DECRYPTION
// ============================================================================

size_t Encryption::encrypt(const uint8_t* plaintext, size_t length,
                           uint8_t* ciphertext, uint8_t* iv) {
    if (!_keySet || !plaintext || !ciphertext || !iv) {
        return 0;
    }
    
    // Generate random IV
    randomBytes(iv, AES_BLOCK_SIZE);
    
    // Calculate padded length
    size_t paddedLen = ((length / AES_BLOCK_SIZE) + 1) * AES_BLOCK_SIZE;
    
    // Create padded buffer
    uint8_t* paddedData = (uint8_t*)malloc(paddedLen);
    if (!paddedData) {
        Serial.println("ERROR: Failed to allocate memory for encryption");
        return 0;
    }
    
    memcpy(paddedData, plaintext, length);
    size_t finalLen;
    addPadding(paddedData, length, &finalLen);
    
    // Encrypt using CBC mode
    int ret = mbedtls_aes_crypt_cbc(&_aesContext, MBEDTLS_AES_ENCRYPT,
                                    finalLen, iv, paddedData, ciphertext);
    
    free(paddedData);
    
    if (ret != 0) {
        Serial.printf("ERROR: Encryption failed (%d)\n", ret);
        return 0;
    }
    
    return finalLen;
}

size_t Encryption::decrypt(const uint8_t* ciphertext, size_t length,
                           uint8_t* plaintext, const uint8_t* iv) {
    if (!_keySet || !ciphertext || !plaintext || !iv) {
        return 0;
    }
    
    if (length % AES_BLOCK_SIZE != 0) {
        Serial.println("ERROR: Invalid ciphertext length");
        return 0;
    }
    
    // Create IV copy (mbedtls modifies it)
    uint8_t ivCopy[AES_BLOCK_SIZE];
    memcpy(ivCopy, iv, AES_BLOCK_SIZE);
    
    // Decrypt
    int ret = mbedtls_aes_crypt_cbc(&_aesContext, MBEDTLS_AES_DECRYPT,
                                    length, ivCopy, ciphertext, plaintext);
    
    if (ret != 0) {
        Serial.printf("ERROR: Decryption failed (%d)\n", ret);
        return 0;
    }
    
    // Remove padding
    size_t originalLen = removePadding(plaintext, length);
    
    return originalLen;
}

// ============================================================================
// HASHING
// ============================================================================

bool Encryption::sha256(const uint8_t* data, size_t length, uint8_t* hash) {
    if (!data || !hash) return false;
    
    int ret = mbedtls_sha256_ret(data, length, hash, 0);
    
    if (ret != 0) {
        Serial.printf("ERROR: SHA256 failed (%d)\n", ret);
        return false;
    }
    
    return true;
}

bool Encryption::hmacSha256(const uint8_t* key, size_t keyLen,
                            const uint8_t* data, size_t dataLen,
                            uint8_t* hmac) {
    if (!key || !data || !hmac) return false;
    
    const mbedtls_md_info_t* mdInfo = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    if (!mdInfo) return false;
    
    int ret = mbedtls_md_hmac(mdInfo, key, keyLen, data, dataLen, hmac);
    
    if (ret != 0) {
        Serial.printf("ERROR: HMAC-SHA256 failed (%d)\n", ret);
        return false;
    }
    
    return true;
}

// ============================================================================
// RANDOM NUMBER GENERATION
// ============================================================================

void Encryption::randomBytes(uint8_t* buffer, size_t length) {
    if (!buffer) return;
    
    for (size_t i = 0; i < length; i++) {
        buffer[i] = (uint8_t)esp_random();
    }
}

// ============================================================================
// SIMPLE XOR ENCRYPTION
// ============================================================================

void Encryption::xorEncrypt(uint8_t* data, size_t length, uint8_t key) {
    if (!data) return;
    
    for (size_t i = 0; i < length; i++) {
        data[i] ^= key;
    }
}

// ============================================================================
// PADDING
// ============================================================================

size_t Encryption::addPadding(uint8_t* data, size_t dataLen, size_t* paddedLen) {
    size_t padding = AES_BLOCK_SIZE - (dataLen % AES_BLOCK_SIZE);
    *paddedLen = dataLen + padding;
    
    // PKCS7 padding
    for (size_t i = 0; i < padding; i++) {
        data[dataLen + i] = (uint8_t)padding;
    }
    
    return *paddedLen;
}

size_t Encryption::removePadding(const uint8_t* data, size_t paddedLen) {
    if (paddedLen == 0) return 0;
    
    uint8_t padding = data[paddedLen - 1];
    
    // Validate padding
    if (padding > AES_BLOCK_SIZE || padding == 0) {
        return paddedLen; // Invalid padding
    }
    
    return paddedLen - padding;
}
