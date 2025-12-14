# Data Integrity Verification with Checksums

This document explains how data integrity is ensured using **CRC32 checksums** across all components of the MQTT Encryption Framework.

## 📋 Overview

Data integrity checks ensure that transmitted sensor data has not been **corrupted** or **tampered with** during transmission. This is critical for:

- ✅ **Detecting transmission errors** (network issues, packet corruption)
- ✅ **Identifying tampering attempts** (man-in-the-middle attacks)
- ✅ **Ensuring data accuracy** (critical for IoT sensor readings)
- ✅ **Compliance and auditing** (proof of data integrity)

## 🔐 Implementation Details

### Architecture

```
┌─────────────┐          ┌──────────────┐          ┌─────────────┐
│  ESP32      │          │ MQTT Broker  │          │  Dashboard  │
│  Sensor     │──────────▶              │──────────▶  /Gateway   │
└─────────────┘          └──────────────┘          └─────────────┘
     │                                                    │
     │ 1. Calculate CRC32                                │
     │ 2. Append to JSON                                 │
     │ 3. Encrypt payload                                │
     │                                                    │
     │                                      1. Decrypt   │
     │                                      2. Verify    │
     │                                      3. Validate  │
```

### Data Format

**Before Encryption:**
```
{"temp":25.50,"hum":60.00,"id":"ESP32_Sensor_001"}|A1B2C3D4
└──────────── JSON Data ─────────────────────────┘ └─ CRC32 ─┘
```

**After Encryption:**
```
[Encrypted Binary Data - AES-128 ECB]
```

### CRC32 Algorithm

We use the **CRC-32** (Cyclic Redundancy Check) algorithm with polynomial `0xEDB88320`:
- **32-bit checksum** provides excellent error detection
- **Standard IEEE 802.3** implementation
- **Hardware-accelerated** on many platforms
- **Collision resistant** for typical IoT payloads

---

## 🔧 Component Implementation

### 1. ESP32 Sensor (Sender)

**File:** `esp32-sensor/main.ino`

#### Checksum Calculation

```cpp
uint32_t calculateCRC32(const unsigned char* data, size_t length) {
  uint32_t crc = 0xFFFFFFFF;
  
  for (size_t i = 0; i < length; i++) {
    crc ^= data[i];
    for (int j = 0; j < 8; j++) {
      if (crc & 1) {
        crc = (crc >> 1) ^ 0xEDB88320;
      } else {
        crc >>= 1;
      }
    }
  }
  
  return ~crc;
}
```

#### Publishing Flow

1. **Create JSON payload** with sensor data
2. **Calculate CRC32** of the JSON string
3. **Append checksum** in format: `data|CHECKSUM`
4. **Encrypt** the combined payload
5. **Publish** to MQTT broker

**Example Output:**
```
✓ Published encrypted data (80 bytes) | Checksum: A1B2C3D4
```

---

### 2. Dashboard (Receiver)

**File:** `dashboard/app.py`

#### Verification Flow

```python
def verify_checksum(data_with_checksum):
    # Split data and checksum
    parts = data_with_checksum.rsplit('|', 1)
    data = parts[0]
    received_checksum = parts[1].strip()
    
    # Calculate expected checksum
    calculated_checksum = calculate_crc32(data)
    
    # Verify match
    is_valid = (received_checksum == calculated_checksum)
    
    return data, is_valid
```

#### Data Processing

1. **Decrypt** the MQTT payload using AES-128
2. **Extract** checksum from decrypted data
3. **Calculate** expected checksum
4. **Compare** received vs calculated
5. **Flag** data as valid/invalid

**Example Output:**
```
[✓] Checksum valid: A1B2C3D4
[📊] ✓ | Temp: 25.50°C | Humidity: 60.00% | ID: ESP32_Sensor_001
```

**Failure Example:**
```
[✗] Checksum MISMATCH! Received: A1B2C3D4, Calculated: B2C3D4E5
[📊] ✗ CHECKSUM FAILED | Temp: 25.50°C | Humidity: 60.00% | ID: ESP32_Sensor_001
```

#### Behavior on Checksum Failure

- ❌ **Data is NOT added to history** (prevents storing corrupted data)
- ⚠️ **Status flag** set to `checksum_error`
- 📝 **Log message** printed to console
- 🔔 **WebSocket broadcast** includes validation status

---

### 3. Raspberry Pi Gateway (Optional)

**File:** `raspberry-pi-gateway/live_ids.py`

The IDS gateway optionally verifies checksums to:
- 🔍 **Detect data corruption** (separate from attack detection)
- 📊 **Track checksum failures** in statistics
- 🚨 **Correlate** integrity issues with attacks

**Configuration:**
```python
ENABLE_CHECKSUM_VERIFICATION = True  # Enable/disable verification
```

**Statistics Output:**
```
==================================================
IDS STATISTICS
==================================================
Total Packets Analyzed: 1250
Attacks Detected: 3
Checksum Failures: 2
IPs Blocked: 1
Attack Rate: 0.24%
==================================================
```

---

## 📊 Checksum Verification Status

### Dashboard Status Indicators

| Status | Meaning | Action Taken |
|--------|---------|--------------|
| ✅ **Valid** | Checksum matches | Data stored in history |
| ❌ **Invalid** | Checksum mismatch | Data flagged, not stored |
| ⚠️ **Missing** | No checksum found | Legacy data, processed normally |

### API Response Format

```json
{
  "temperature": 25.50,
  "humidity": 60.00,
  "sensor_id": "ESP32_Sensor_001",
  "timestamp": "2025-12-13 23:45:12",
  "status": "connected",
  "checksum_valid": true
}
```

---

## 🧪 Testing Checksum Verification

### Test 1: Normal Operation

1. **Start** the ESP32 sensor
2. **Verify** dashboard shows `✓` checksum indicators
3. **Confirm** data is being stored in history

**Expected Output:**
```
[✓] Checksum valid: A1B2C3D4
[📊] ✓ | Temp: 25.50°C | Humidity: 60.00%
```

### Test 2: Simulate Corruption

To test checksum failure detection, you can modify the dashboard code temporarily:

```python
# In on_mqtt_message(), after decryption:
decrypted_data = decrypted_data.replace('|', '|CORRUPTED')  # Corrupt checksum
```

**Expected Output:**
```
[✗] Checksum MISMATCH! Received: CORRUPTED, Calculated: A1B2C3D4
[📊] ✗ CHECKSUM FAILED | Temp: 25.50°C | Humidity: 60.00%
```

### Test 3: Gateway Statistics

Run the gateway and monitor for checksum failures:

```bash
sudo python3 live_ids.py
# Press Ctrl+C after some time
```

**Shutdown statistics will show:**
```
Checksum Failures: 0  # Should be 0 in normal operation
```

---

## 🔍 Troubleshooting

### Issue: All checksums failing

**Possible Causes:**
1. ❌ **Old ESP32 code** without checksum support
2. ❌ **Mismatch** in CRC32 implementation
3. ❌ **Character encoding** differences

**Solution:**
- Re-upload the updated ESP32 code
- Verify both sender and receiver use the same CRC32 algorithm
- Ensure UTF-8 encoding on both sides

### Issue: Intermittent checksum failures

**Possible Causes:**
1. 📡 **Network packet corruption** (WiFi interference)
2. 🐛 **Buffer overflow** issues
3. ⚡ **Power supply instability** on ESP32

**Solution:**
- Improve WiFi signal strength
- Check ESP32 power supply (use 5V/2A adapter)
- Add retry logic for failed transmissions

### Issue: Dashboard not showing checksum status

**Possible Causes:**
1. 📦 **Old payload format** (pre-checksum)
2. 🔧 **Configuration disabled**

**Solution:**
- Verify ESP32 firmware is updated
- Check data format in console logs

---

## 📈 Performance Impact

### ESP32

- **Computation time:** ~50-100 microseconds for typical payload
- **Memory overhead:** Minimal (32-bit checksum)
- **Network overhead:** +9 bytes per message ("|" + 8 hex chars)

### Dashboard/Gateway

- **CPU usage:** Negligible (<1% increase)
- **Latency:** <1ms checksum verification
- **Memory:** No significant impact

---

## 🔒 Security Considerations

### What Checksums Protect Against

✅ **Accidental corruption** (bit flips, network errors)  
✅ **Non-targeted tampering** detection  
✅ **Data integrity** validation

### What Checksums DON'T Protect Against

❌ **Cryptographic attacks** (checksums are not MACs)  
❌ **Sophisticated tampering** (attacker can recalculate checksum)  
❌ **Replay attacks** (use timestamps/nonces separately)

### Enhancement Options

For stronger integrity protection, consider:

1. **HMAC-SHA256** instead of CRC32 (cryptographic MAC)
2. **Message sequence numbers** (prevent replay)
3. **Timestamps** with time-window validation
4. **Digital signatures** for non-repudiation

---

## 📝 Best Practices

1. ✅ **Always verify checksums** on the receiver side
2. ✅ **Log checksum failures** for analysis
3. ✅ **Monitor failure rates** (high rates indicate issues)
4. ✅ **Reject corrupted data** (don't store or act on it)
5. ✅ **Combine with encryption** (CRC32 alone is not secure)

---

## 🎓 Additional Resources

- [CRC Wikipedia](https://en.wikipedia.org/wiki/Cyclic_redundancy_check)
- [RFC 3385 - CRC-32](https://datatracker.ietf.org/doc/html/rfc3385)
- [MQTT Message Integrity](https://www.hivemq.com/blog/mqtt-security-fundamentals/)

---

## 📞 Support

For issues or questions:
1. Check the console logs for checksum status
2. Verify all components are running updated code
3. Test with a minimal setup first
4. Review the troubleshooting section above
