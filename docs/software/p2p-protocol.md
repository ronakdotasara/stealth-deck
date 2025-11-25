# File 89: docs/software/p2p-protocol.md

```markdown
# Stealth Deck - P2P Protocol Specification

Peer-to-peer transfer protocol for secure file and data exchange.

---

## Protocol Overview

### Purpose

Enable secure, encrypted peer-to-peer transfers between Stealth Deck devices using Bluetooth SPP.

### Key Features

- Encrypted transfers (AES-256-GCM)
- Chunked transmission
- Resume capability
- Progress tracking
- Multiple data types
- Authentication

---

## Connection Establishment

### Discovery Phase

```
Device A                          Device B
   |                                 |
   |-- Bluetooth Scan -------------->|
   |<-- Advertisement ---------------|
   |                                 |
   |-- Connection Request ---------->|
   |<-- Connection Accept ---------- |
   |                                 |
```

### Pairing Phase

```
Device A                          Device B
   |                                 |
   |-- Public Key ------------------>|
   |<-- Public Key -----------------|
   |                                 |
   |-- Verify Fingerprint            |
   |    (User confirms)              |
   |                                 |
   |-- Session Key Exchange -------->|
   |<-- ACK -------------------------|
   |                                 |
```

---

## Message Format

### Frame Structure

```
┌──────┬──────────┬──────────┬──────────┬─────────┬─────────┐
│ TYPE │ LENGTH_H │ LENGTH_L │ SEQ_NUM  │ PAYLOAD │  CRC16  │
│ 1B   │ 1B       │ 1B       │ 2B       │ 0-1024B │ 2B      │
└──────┴──────────┴──────────┴──────────┴─────────┴─────────┘
```

### Field Descriptions

| Field | Size | Description |
|-------|------|-------------|
| TYPE | 1 byte | Message type identifier |
| LENGTH | 2 bytes | Payload length (big-endian) |
| SEQ_NUM | 2 bytes | Sequence number |
| PAYLOAD | Variable | Message data (encrypted) |
| CRC16 | 2 bytes | Checksum |

---

## Message Types

### Control Messages

#### 0x10 - HELLO
Initial greeting and capability exchange.

**Payload:**
```
┌────────────┬──────────┬──────────────┐
│ VERSION(1) │ FLAGS(1) │ DEVICE_ID(16)│
└────────────┴──────────┴──────────────┘

FLAGS:
  Bit 0: Supports encryption
  Bit 1: Supports resume
  Bit 2: Supports compression
  Bit 3-7: Reserved
```

#### 0x11 - KEY_EXCHANGE
Exchange encryption keys.

**Payload:**
```
┌──────────────┬──────────────┐
│ PUBLIC_KEY   │ KEY_HASH(16) │
│ (32 bytes)   │              │
└──────────────┴──────────────┘
```

#### 0x12 - READY
Signal ready to transfer.

**Payload:**
```
┌────────────┐
│ STATUS (1) │
└────────────┘

STATUS:
  0x00 = Ready
  0x01 = Not ready
```

### Transfer Messages

#### 0x20 - TRANSFER_START
Initiate file transfer.

**Payload:**
```
┌──────────────┬────────────┬────────────┬──────────┬──────────┐
│ FILE_SIZE(4) │ CHUNKS(2)  │ TYPE(1)    │NAME_LEN  │ FILENAME │
└──────────────┴────────────┴────────────┴──────────┴──────────┘

TYPE:
  0x00 = File
  0x01 = Text
  0x02 = Image
  0x03 = Camera
```

#### 0x21 - CHUNK_DATA
Send data chunk.

**Payload:**
```
┌────────────┬────────────┬──────────────┐
│ CHUNK_ID(2)│ SIZE(2)    │ CHUNK_DATA   │
└────────────┴────────────┴──────────────┘

Encrypted with session key
```

#### 0x22 - CHUNK_ACK
Acknowledge chunk received.

**Payload:**
```
┌────────────┐
│ CHUNK_ID(2)│
└────────────┘
```

#### 0x23 - CHUNK_NACK
Request chunk retransmission.

**Payload:**
```
┌────────────┬────────────┐
│ CHUNK_ID(2)│ REASON(1)  │
└────────────┴────────────┘

REASON:
  0x01 = CRC error
  0x02 = Decrypt error
  0x03 = Out of sequence
```

#### 0x24 - TRANSFER_COMPLETE
Signal transfer completion.

**Payload:**
```
┌────────────┬────────────┐
│ CRC32(4)   │ STATUS(1)  │
└────────────┴────────────┘

STATUS:
  0x00 = Success
  0x01 = Failed
  0x02 = Cancelled
```

#### 0x25 - PAUSE
Pause transfer.

**Payload:**
```
┌────────────┐
│ REASON(1)  │
└────────────┘
```

#### 0x26 - RESUME
Resume paused transfer.

**Payload:**
```
┌────────────┐
│ CHUNK_ID(2)│
└────────────┘
```

---

## Transfer Flow

### Successful Transfer

```
Sender                            Receiver
  |                                  |
  |-- HELLO ------------------------>|
  |<-- HELLO ----------------------- |
  |                                  |
  |-- KEY_EXCHANGE ----------------->|
  |<-- KEY_EXCHANGE ----------------|
  |                                  |
  |-- READY ------------------------>|
  |<-- READY -----------------------|
  |                                  |
  |-- TRANSFER_START --------------->|
  |<-- CHUNK_ACK (ready) -----------|
  |                                  |
  |-- CHUNK_DATA (0) --------------->|
  |<-- CHUNK_ACK (0) ---------------|
  |                                  |
  |-- CHUNK_DATA (1) --------------->|
  |<-- CHUNK_ACK (1) ---------------|
  |                                  |
  |   ... (more chunks) ...          |
  |                                  |
  |-- TRANSFER_COMPLETE ------------>|
  |<-- CHUNK_ACK (complete) --------|
  |                                  |
```

### Transfer with Retransmission

```
Sender                            Receiver
  |                                  |
  |-- CHUNK_DATA (5) --------------->|
  |<-- CHUNK_NACK (5, CRC error) ---|
  |                                  |
  |-- CHUNK_DATA (5) [retry] ------->|
  |<-- CHUNK_ACK (5) ---------------|
  |                                  |
```

### Pause and Resume

```
Sender                            Receiver
  |                                  |
  |-- CHUNK_DATA (10) -------------->|
  |<-- PAUSE -----------------------|
  |                                  |
  |   [Paused state]                 |
  |                                  |
  |<-- RESUME (from chunk 11) ------|
  |                                  |
  |-- CHUNK_DATA (11) -------------->|
  |<-- CHUNK_ACK (11) --------------|
  |                                  |
```

---

## Encryption

### Session Key Generation

1. Both devices generate ephemeral key pairs
2. Exchange public keys
3. Derive shared secret using key exchange
4. Use shared secret as session key

### Data Encryption

- **Algorithm**: AES-256-GCM
- **Key**: Session key (32 bytes)
- **Nonce**: Random 12 bytes per chunk
- **AAD**: None

### Encrypted Payload Format

```
┌──────────┬──────────────┬─────────┐
│ NONCE(12)│ CIPHERTEXT   │ TAG(16) │
└──────────┴──────────────┴─────────┘
```

---

## Error Handling

### Timeout Values

| Operation | Timeout |
|-----------|---------|
| Connection | 30 seconds |
| Key exchange | 10 seconds |
| Chunk ACK | 5 seconds |
| Transfer complete | 60 seconds |

### Retry Strategy

```
Attempt 1: Wait 1 second
Attempt 2: Wait 2 seconds
Attempt 3: Wait 5 seconds
After 3 failures: Abort transfer
```

### Error Codes

| Code | Description |
|------|-------------|
| 0x01 | CRC mismatch |
| 0x02 | Decryption failed |
| 0x03 | Out of sequence |
| 0x04 | Timeout |
| 0x05 | Insufficient space |
| 0x06 | Connection lost |
| 0x07 | User cancelled |

---

## Performance Characteristics

### Throughput

| Condition | Speed |
|-----------|-------|
| Bluetooth SPP | ~100 KB/s |
| With encryption | ~80 KB/s |
| Optimal | 1MB in ~12 seconds |

### Overhead

- Frame overhead: ~8 bytes per chunk
- Encryption overhead: ~28 bytes per chunk
- ACK overhead: ~6 bytes per chunk
- **Total**: ~42 bytes per 1024-byte chunk (4%)

---

## Security Considerations

### Key Exchange

- Uses ephemeral keys (per-session)
- Key fingerprint verification recommended
- Session keys cleared after transfer

### Authentication

- Device ID verification
- Key fingerprint display for manual verification
- Optional PIN code pairing

### Data Protection

- All data encrypted in transit
- Authentication tags prevent tampering
- Secure deletion after transfer (optional)

---

## Implementation Notes

### Sender

```
# Initialize
session_key = generate_session_key()
send_key_exchange(session_key)

# Start transfer
metadata = prepare_transfer(file_path)
send_transfer_start(metadata)

# Send chunks
for chunk in file_chunks:
    encrypted_chunk = encrypt(chunk, session_key)
    send_chunk_data(chunk_id, encrypted_chunk)
    wait_for_ack(chunk_id)

# Complete
send_transfer_complete(checksum)
```

### Receiver

```
# Initialize
receive_key_exchange()
session_key = derive_session_key()

# Receive transfer
metadata = receive_transfer_start()
prepare_file(metadata)

# Receive chunks
while not complete:
    chunk = receive_chunk_data()
    decrypted = decrypt(chunk, session_key)
    write_chunk(chunk_id, decrypted)
    send_chunk_ack(chunk_id)

# Verify
verify_checksum(file, expected_checksum)
```

---

## Testing

### Test Cases

1. **Basic Transfer**: Single file, no errors
2. **Large File**: 10MB file, verify chunking
3. **Error Recovery**: Inject CRC errors, verify retransmission
4. **Pause/Resume**: Pause mid-transfer, resume successfully
5. **Connection Loss**: Simulate disconnect, verify cleanup
6. **Concurrent Transfers**: Multiple files in sequence

---

**Version**: 1.0  
**Last Updated**: 2025-11-25  
**Status**: Stable
```

***

