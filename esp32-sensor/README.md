# ESP32 Sensor Node

This component reads real-time sensor data (temperature and humidity), encrypts it using **AES-128**, and publishes it securely to an MQTT broker.

## 📋 Hardware Requirements

- **ESP32 Development Board** (ESP32-DevKitC or similar)
- **DHT22** or **DHT11** Temperature/Humidity Sensor
- **Jumper Wires**
- **USB Cable** for programming

## 🔌 Wiring Diagram

```
DHT22 Sensor -> ESP32
----------------------------
VCC (Pin 1)  -> 3.3V
DATA (Pin 2) -> GPIO 4
NC (Pin 3)   -> (Not Connected)
GND (Pin 4)  -> GND
```

**Note:** Add a 10kΩ pull-up resistor between VCC and DATA pins for stable operation.

## 📚 Required Libraries

Install the following libraries via **Arduino IDE Library Manager**:

1. **WiFi** (Built-in with ESP32 board package)
2. **PubSubClient** by Nick O'Leary
3. **mbedtls** (Built-in with ESP32)
4. **DHT sensor library** by Adafruit
5. **Adafruit Unified Sensor** (dependency for DHT library)

## ⚙️ Configuration

### Option 1: Local MQTT Broker (Raspberry Pi/Mosquitto)

Open `main.ino` and update:

```cpp
// WiFi Credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// MQTT Broker Settings (Local)
const char* MQTT_BROKER = "192.168.1.100";  // Your Raspberry Pi IP
const int MQTT_PORT = 1883;                 // Standard MQTT port
const char* MQTT_USERNAME = "";             // Leave empty if no auth
const char* MQTT_PASSWORD = "";             // Leave empty if no auth

// AES Key (MUST match gateway and dashboard)
unsigned char AES_KEY[16] = {
  0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
  0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
};
```

**Note:** For local brokers, you typically use port `1883` without TLS.

---

### Option 2: HiveMQ Cloud (Recommended for Production)

#### Step 1: Create HiveMQ Cloud Account

1. Go to https://console.hivemq.cloud/
2. Sign up for a free account
3. Create a new cluster (free tier: 100 connections, 10GB/month)
4. Note your **Cluster URL** (e.g., `abc123xyz.s1.eu.hivemq.cloud`)

#### Step 2: Create Credentials

1. In your HiveMQ cluster dashboard, go to **"Access Management"**
2. Click **"Add Credentials"**
3. Create credentials for ESP32:
   - **Username**: `esp32_user` (or your choice)
   - **Password**: Create a strong password
4. **Optional:** Set permissions:
   - Allow **Publish** to topic pattern: `home/sensor/#`
5. **Save the credentials** - you'll need them!

#### Step 3: Update ESP32 Code

Open `main.ino` and configure for HiveMQ Cloud:

```cpp
#include <WiFiClientSecure.h>  // Use secure client for TLS

// WiFi Credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// HiveMQ Cloud Settings
const char* MQTT_BROKER = "abc123xyz.s1.eu.hivemq.cloud";  // Your cluster URL
const int MQTT_PORT = 8883;                                 // TLS port
const char* MQTT_USERNAME = "esp32_user";                   // From Access Management
const char* MQTT_PASSWORD = "your_strong_password";         // From Access Management

// AES Key (MUST match gateway and dashboard)
unsigned char AES_KEY[16] = {
  0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
  0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
};
```

#### Step 4: Enable TLS in Code

Find the WiFi client initialization section and update:

```cpp
// For HiveMQ Cloud (TLS)
WiFiClientSecure espClient;
PubSubClient client(espClient);

void setup() {
  // ...
  
  // Skip certificate validation (for testing - use proper certs in production!)
  espClient.setInsecure();
  
  // Set MQTT server
  client.setServer(MQTT_BROKER, MQTT_PORT);
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Connecting to HiveMQ Cloud...");
    
    // Connect with username and password
    if (client.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("✓ Connected to HiveMQ Cloud!");
    } else {
      Serial.print("✗ Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}
```

**Important Changes:**
- Replace `WiFiClient` with `WiFiClientSecure`
- Add `espClient.setInsecure()` to skip certificate validation (testing only)
- Use port `8883` for TLS
- Provide username and password in `client.connect()`

#### Step 5: Test Connection

1. Upload the code to ESP32
2. Open Serial Monitor (115200 baud)
3. You should see:
   ```
   Connecting to HiveMQ Cloud...
   ✓ Connected to HiveMQ Cloud!
   ✓ Published encrypted data (64 bytes)
   ```

#### Verify in HiveMQ Dashboard

1. Go to your HiveMQ cluster dashboard
2. Check **"Web Client"** tab
3. Click **"Connect"**
4. Subscribe to topic: `home/sensor/data`
5. You should see encrypted messages arriving!

---

### 🔒 Security Notes

**For Testing:**
```cpp
espClient.setInsecure();  // Skip certificate validation
```

**For Production (Recommended):**
Download HiveMQ root CA certificate and use:
```cpp
const char* root_ca = R"(
-----BEGIN CERTIFICATE-----
[Your HiveMQ CA certificate here]
-----END CERTIFICATE-----
)";

espClient.setCACert(root_ca);  // Validate server certificate
```

---

### 📋 Configuration Summary

| Setting | Local Broker | HiveMQ Cloud |
|---------|-------------|--------------|
| **MQTT_BROKER** | `192.168.1.100` | `abc123xyz.s1.eu.hivemq.cloud` |
| **MQTT_PORT** | `1883` | `8883` |
| **Client Type** | `WiFiClient` | `WiFiClientSecure` |
| **TLS** | No | Yes (required) |
| **Username/Password** | Optional | Required |
| **Certificate** | Not needed | Optional (recommended) |

## 🚀 Upload Instructions

1. **Install ESP32 Board Package:**
   - In Arduino IDE, go to `File > Preferences`
   - Add this URL to "Additional Board Manager URLs":
     ```
     https://dl.espressif.com/dl/package_esp32_index.json
     ```
   - Go to `Tools > Board > Boards Manager`
   - Search for "ESP32" and install "ESP32 by Espressif Systems"

2. **Select Board:**
   - `Tools > Board > ESP32 Arduino > ESP32 Dev Module`

3. **Select Port:**
   - `Tools > Port > (Select your ESP32 COM port)`

4. **Upload:**
   - Click the **Upload** button (→)

## 📊 Serial Monitor Output

After uploading, open the Serial Monitor (`115200 baud`) to see:

```
=== ESP32 Secure MQTT Sensor Node ===
DHT sensor initialized
Connecting to WiFi: MyNetwork
WiFi connected!
IP Address: 192.168.1.150
Signal Strength (RSSI): -45 dBm
Setup complete!

Connecting to MQTT broker... Connected!
Temperature: 23.50°C | Humidity: 45.20%
✓ Published encrypted data (64 bytes)
Temperature: 23.60°C | Humidity: 45.30%
✓ Published encrypted data (64 bytes)
```

## 🔒 Security Features

- **AES-128 Encryption:** All sensor data is encrypted before transmission
- **Secure Key Storage:** Encryption key is embedded in firmware
- **MQTT Authentication:** Optional username/password support

## 📡 MQTT Topic Structure

```
home/sensor/data  →  Encrypted sensor readings
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Failed to connect to WiFi | Check SSID/password, ensure 2.4GHz network |
| Failed to read from DHT sensor | Check wiring, add pull-up resistor |
| MQTT connection failed | Verify broker IP, check firewall settings |
| Upload failed | Select correct COM port, press BOOT button during upload |

## 📝 Notes

- The sensor publishes data every **5 seconds** by default (configurable)
- Encrypted payload is padded to a multiple of 16 bytes (AES block size)
- JSON format: `{"temp":23.5,"hum":45.2,"id":"ESP32_Sensor_001"}`
