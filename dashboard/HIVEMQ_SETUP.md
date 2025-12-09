# HiveMQ Cloud Setup Guide

This guide will help you configure your MQTT IoT Dashboard to use HiveMQ Cloud.

## 📋 Prerequisites

- Python 3.7+ installed
- Internet connection
- Email for HiveMQ account

## 🚀 Step 1: Create HiveMQ Cloud Account

1. **Visit HiveMQ Console**
   - Navigate to: https://console.hivemq.cloud/
   - Click "Sign Up" (or "Get Started Free")

2. **Create Account**
   - Enter your email and password
   - Verify your email address
   - Log in to the HiveMQ Cloud console

3. **Create a Cluster (Free Tier)**
   - Click "Create Cluster" or "Create New Cluster"
   - Choose **Free** tier (100 connections, 10GB/month)
   - Select a region close to you (e.g., EU-Central, US-East)
   - Give your cluster a name (e.g., "IoT-Dashboard")
   - Click "Create"

4. **Get Your Cluster URL**
   - After creation, you'll see your cluster details
   - **Copy the Cluster URL** - it looks like: `abc123xyz.s1.eu.hivemq.cloud`
   - Note: Port for TLS connections is **8883**

5. **Create Credentials**
   - In your cluster dashboard, go to "Access Management"
   - Click "Add Credentials" or "Create Credentials"
   - Choose a **Username** (e.g., `dashboard_user`)
   - Set a **Password** (strong password recommended)
   - Click "Create"
   - **Save these credentials** - you'll need them!

## 🔧 Step 2: Configure Dashboard

1. **Install Dependencies**

```bash
cd dashboard
pip install -r requirements.txt
```

2. **Create .env File**

Copy the example file:

```bash
copy .env.example .env
```

3. **Edit .env File**

Open `.env` in a text editor and update with your HiveMQ credentials:

```env
# Flask Configuration
FLASK_SECRET_KEY=mqtt-iot-dashboard-2024-secure-key

# HiveMQ Cloud Configuration
MQTT_BROKER=abc123xyz.s1.eu.hivemq.cloud    # Your cluster URL
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_USERNAME=dashboard_user                  # Your HiveMQ username
MQTT_PASSWORD=your_strong_password           # Your HiveMQ password

# Topic Configuration
MQTT_TOPIC=home/sensor/data
MQTT_CLIENT_ID=Dashboard_Client
```

4. **Run Dashboard**

```bash
python app.py
```

You should see:
```
[🔒] TLS/SSL encryption enabled
[🔑] Authentication enabled for user: dashboard_user
[*] Connecting to MQTT broker: abc123xyz.s1.eu.hivemq.cloud:8883
[✓] Dashboard connected to MQTT broker
```

5. **Access Dashboard**

Open your browser: `http://localhost:5000`

## 📡 Step 3: Configure ESP32

Update your ESP32 code to connect to HiveMQ Cloud.

**Required Changes in `main.ino`:**

```cpp
#include <WiFiClientSecure.h>

// HiveMQ Cloud Configuration
const char* MQTT_BROKER = "abc123xyz.s1.eu.hivemq.cloud";  // Your cluster URL
const int MQTT_PORT = 8883;                                // TLS port
const char* MQTT_USERNAME = "esp32_user";                  // Create separate user
const char* MQTT_PASSWORD = "your_password";               // HiveMQ password

// Use secure WiFi client
WiFiClientSecure espClient;
PubSubClient client(espClient);

void setup() {
  // ...
  
  // Skip certificate validation (for testing only!)
  espClient.setInsecure();
  
  // Set MQTT server
  client.setServer(MQTT_BROKER, MQTT_PORT);
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Connecting to HiveMQ Cloud...");
    
    // Connect with username and password
    if (client.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("Connected to HiveMQ Cloud!");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}
```

## 🧪 Step 4: Test Connection

### Test via HiveMQ Web Client

1. Go to your cluster dashboard
2. Click "Web Client" tab
3. Click "Connect"
4. Subscribe to topic: `home/sensor/data`
5. Run your ESP32 - you should see messages appear!

### Test via Dashboard

1. Start dashboard: `python app.py`
2. Power on ESP32
3. Open browser: `http://localhost:5000`
4. You should see real-time temperature/humidity updates!

## 🔒 Security Best Practices

### 1. **Use Different Credentials for Different Devices**

Create separate users in HiveMQ for:
- Dashboard (subscribe only)
- ESP32 (publish only)
- Raspberry Pi (if used as gateway)

### 2. **Set Permissions (ACL)**

In HiveMQ dashboard:
- **esp32_user**: Publish to `home/sensor/#` only
- **dashboard_user**: Subscribe to `home/sensor/#` only

### 3. **Use Certificate Validation (Production)**

For production, replace `espClient.setInsecure()` with proper certificate validation:

```cpp
// Download HiveMQ root CA certificate
const char* root_ca = R"(
-----BEGIN CERTIFICATE-----
[Your HiveMQ CA certificate]
-----END CERTIFICATE-----
)";

espClient.setCACert(root_ca);
```

## 🐳 Docker Deployment with HiveMQ

Build and run with environment variables:

```bash
docker build -t mqtt-dashboard .

docker run -d -p 5000:5000 \
  -e MQTT_BROKER=abc123xyz.s1.eu.hivemq.cloud \
  -e MQTT_PORT=8883 \
  -e MQTT_USE_TLS=true \
  -e MQTT_USERNAME=dashboard_user \
  -e MQTT_PASSWORD=your_password \
  --name mqtt-dashboard \
  mqtt-dashboard
```

## 🌐 Cloud Dashboard Deployment

When deploying dashboard to cloud (AWS/GCP), set environment variables in your platform:

**AWS EC2 / Elastic Beanstalk:**
```bash
export MQTT_BROKER=abc123xyz.s1.eu.hivemq.cloud
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export MQTT_USERNAME=dashboard_user
export MQTT_PASSWORD=your_password
```

**Google Cloud Run:**
```bash
gcloud run deploy mqtt-dashboard \
  --set-env-vars MQTT_BROKER=abc123xyz.s1.eu.hivemq.cloud,MQTT_PORT=8883,MQTT_USE_TLS=true,MQTT_USERNAME=dashboard_user,MQTT_PASSWORD=your_password
```

## 🐛 Troubleshooting

### Connection Failed

**Error:** `Failed, rc=-2`
- **Solution**: Check WiFi connection, verify broker URL

**Error:** `Failed, rc=5` (Connection Refused)
- **Solution**: Check username/password are correct

**Error:** `Failed, rc=4` (Bad Username/Password)
- **Solution**: Verify credentials in HiveMQ dashboard

### TLS Errors

**Error:** `SSL handshake failed`
- **Solution**: Ensure `setInsecure()` is called or proper CA cert is set

### No Messages Received

1. Check ESP32 is connected and publishing
2. Verify topic names match exactly: `home/sensor/data`
3. Check HiveMQ Web Client to confirm messages are arriving
4. Verify dashboard is subscribed to correct topic

## 📊 Monitoring

### HiveMQ Cloud Dashboard

Monitor your cluster:
- **Connections**: See active clients (ESP32, Dashboard)
- **Messages**: View message throughput
- **Data Transfer**: Monitor bandwidth usage
- **Logs**: Check connection/disconnection events

### Dashboard Logs

The dashboard prints detailed logs:
```
[🔒] TLS/SSL encryption enabled
[🔑] Authentication enabled for user: dashboard_user
[*] Connecting to MQTT broker: abc123xyz.s1.eu.hivemq.cloud:8883
[✓] Dashboard connected to MQTT broker
[✓] Subscribed to topic: home/sensor/data
[📊] Temp: 24.5°C | Humidity: 55% | ID: ESP32_Sensor_001
```

## 💡 Tips

1. **Free Tier Limits**: 100 connections, 10GB/month is plenty for small projects
2. **Low Latency**: Choose HiveMQ region closest to your devices
3. **Backup**: Keep local Mosquitto as backup broker
4. **Testing**: Use HiveMQ Web Client for debugging before touching code
5. **Security**: Never commit `.env` file to Git (already in `.gitignore`)

## 🎉 Success!

Once configured:
- ✅ No more IP address changes to worry about
- ✅ Access from anywhere with internet
- ✅ Professional monitoring and uptime
- ✅ TLS encryption by default
- ✅ Easy to deploy to cloud platforms

Need help? Check HiveMQ documentation: https://docs.hivemq.com/
