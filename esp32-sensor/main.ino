/*
 * ESP32 Secure MQTT Sensor Node
 * 
 * This code reads temperature data from a sensor, encrypts it using AES-128,
 * and publishes it securely to an MQTT broker.
 * 
 * Hardware Required:
 * - ESP32 Development Board
 * - DHT22 or DHT11 Temperature/Humidity Sensor
 * 
 * Libraries Required (Install via Arduino Library Manager):
 * - WiFi (Built-in with ESP32)
 * - PubSubClient by Nick O'Leary
 * - mbedtls (Built-in with ESP32)
 * - DHT sensor library by Adafruit
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>  // Required for TLS/SSL (HiveMQ Cloud)
#include <PubSubClient.h>
#include <mbedtls/aes.h>
#include <DHT.h>

// ==================== CONFIGURATION ====================

// WiFi Credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";      // Replace with your WiFi network name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";  // Replace with your WiFi password

// MQTT Broker Settings
const char* MQTT_BROKER = "dc98974a1edd4d5883e377908c3b6d87.s1.eu.hivemq.cloud";  // e.g., "192.168.1.100" or cloud IP
const int MQTT_PORT = 8883;
const char* MQTT_CLIENT_ID = "ESP32_Sensor_001";
const char* MQTT_USERNAME = "esp32_user";             
const char* MQTT_PASSWORD = "Esp32_pwd";     

// MQTT Topic
const char* MQTT_TOPIC = "home/sensor/data";

// AES-128 Encryption Key (16 bytes)
// IMPORTANT: This MUST match the key used on the gateway and dashboard
unsigned char AES_KEY[16] = {
  0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
  0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
};

// DHT Sensor Configuration
#define DHT_PIN 4           // GPIO pin connected to DHT sensor
#define DHT_TYPE DHT22      // DHT22 (AM2302) or DHT11

// Timing Configuration
#define PUBLISH_INTERVAL 5000  // Publish every 5 seconds (in milliseconds)

// ==================== GLOBAL OBJECTS ====================

// For HiveMQ Cloud with TLS (port 8883)
WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHT_PIN, DHT_TYPE);

// ==================== FUNCTION PROTOTYPES ====================

void setupWiFi();
void reconnectMQTT();
void encryptAES(unsigned char* plaintext, size_t length, unsigned char* ciphertext);
void publishEncryptedData(float temperature, float humidity);

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== ESP32 Secure MQTT Sensor Node ===");
  
  // Initialize DHT sensor
  dht.begin();
  Serial.println("DHT sensor initialized");
  
  // Connect to WiFi
  setupWiFi();
  
  // Configure TLS for HiveMQ Cloud (skip certificate validation for testing)
  // For production, use proper certificate validation
  espClient.setInsecure();
  Serial.println("TLS configured (certificate validation disabled)");
  
  // Configure MQTT broker
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  
  Serial.println("Setup complete!\n");
}

// ==================== MAIN LOOP ====================

void loop() {
  // Ensure MQTT connection is active
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  // Read sensor data
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();  // Celsius
  
  // Check if readings are valid
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }
  
  // Display readings
  Serial.printf("Temperature: %.2f°C | Humidity: %.2f%%\n", temperature, humidity);
  
  // Publish encrypted data
  publishEncryptedData(temperature, humidity);
  
  // Wait before next reading
  delay(PUBLISH_INTERVAL);
}

// ==================== FUNCTION IMPLEMENTATIONS ====================

/**
 * Connect to WiFi network
 */
void setupWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;
    
    if (attempts > 60) {  // 30 seconds timeout
      Serial.println("\nFailed to connect to WiFi! Restarting...");
      ESP.restart();
    }
  }
  
  Serial.println("\nWiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Signal Strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}

/**
 * Reconnect to MQTT broker
 */
void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT broker...");
    
    // Attempt to connect
    bool connected;
    if (strlen(MQTT_USERNAME) > 0) {
      connected = mqttClient.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD);
    } else {
      connected = mqttClient.connect(MQTT_CLIENT_ID);
    }
    
    if (connected) {
      Serial.println(" Connected!");
    } else {
      Serial.print(" Failed (rc=");
      Serial.print(mqttClient.state());
      Serial.println("). Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

/**
 * Encrypt data using AES-128 ECB mode
 * 
 * @param plaintext Input data to encrypt
 * @param length Length of plaintext (must be multiple of 16)
 * @param ciphertext Output encrypted data
 */
void encryptAES(unsigned char* plaintext, size_t length, unsigned char* ciphertext) {
  mbedtls_aes_context aes;
  mbedtls_aes_init(&aes);
  mbedtls_aes_setkey_enc(&aes, AES_KEY, 128);
  
  // Encrypt in 16-byte blocks
  for (size_t i = 0; i < length; i += 16) {
    mbedtls_aes_crypt_ecb(&aes, MBEDTLS_AES_ENCRYPT, plaintext + i, ciphertext + i);
  }
  
  mbedtls_aes_free(&aes);
}

/**
 * Publish encrypted sensor data to MQTT
 * 
 * @param temperature Temperature reading in Celsius
 * @param humidity Humidity reading in percentage
 */
void publishEncryptedData(float temperature, float humidity) {
  // Create JSON payload
  char payload[64];
  snprintf(payload, sizeof(payload), 
           "{\"temp\":%.2f,\"hum\":%.2f,\"id\":\"%s\"}", 
           temperature, humidity, MQTT_CLIENT_ID);
  
  size_t payload_len = strlen(payload);
  
  // Pad to multiple of 16 bytes (AES block size)
  size_t padded_len = ((payload_len / 16) + 1) * 16;
  unsigned char plaintext[padded_len];
  unsigned char ciphertext[padded_len];
  
  // Copy payload and pad with zeros
  memset(plaintext, 0, padded_len);
  memcpy(plaintext, payload, payload_len);
  
  // Encrypt the data
  encryptAES(plaintext, padded_len, ciphertext);
  
  // Publish encrypted data
  bool success = mqttClient.publish(MQTT_TOPIC, ciphertext, padded_len);
  
  if (success) {
    Serial.printf("✓ Published encrypted data (%d bytes)\n", padded_len);
  } else {
    Serial.println("✗ Failed to publish!");
  }
}
