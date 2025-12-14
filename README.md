# 🔒 Secure MQTT IoT System

A comprehensive end-to-end secure IoT system with **AES-128 encryption**, **ML-based intrusion detection**, and **real-time visualization**. Built for ESP32 sensors, Raspberry Pi gateway, and cloud-deployable dashboard.

![System Architecture](https://img.shields.io/badge/Architecture-Distributed-blue)
![Security](https://img.shields.io/badge/Security-AES--128-green)
![ML](https://img.shields.io/badge/ML-Intrusion%20Detection-orange)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

---

## 🎯 Project Overview

This project implements a **three-tier secure IoT architecture** with:

1. **ESP32 Sensor Nodes** → Collect and encrypt data
2. **Raspberry Pi Gateway** → ML-based intrusion detection & firewall
3. **Web Dashboard** → Real-time visualization with decryption

### 🔐 Security Features

- **End-to-End AES-128 Encryption** on MQTT payloads
- **CRC32 Checksum Verification** for data integrity validation
- **Machine Learning IDS** using Decision Tree classifier
- **Automatic IP Blocking** via iptables firewall
- **Attack Logging** and real-time monitoring
- **Feature Engineering** based on RT-IoT2022 dataset

---

## 📁 Repository Structure

```
Mqtt_Encryption_Framework/
│
├── esp32-sensor/                    # ESP32 Sensor Node (Arduino C++)
│   ├── main.ino                     # Main firmware code
│   └── README.md                    # Sensor setup and wiring guide
│
├── raspberry-pi-gateway/            # Raspberry Pi Edge Gateway (Python)
│   ├── live_ids.py                  # Real-time IDS with ML detection + IP blocking
│   ├── collect_normal_data.py       # Collect benign traffic for training
│   ├── collect_attack_data.py       # Generate and collect attack data
│   ├── attack_simulator.py          # Attack simulation tool (testing)
│   ├── requirements.txt             # Python dependencies
│   └── README.md                    # Installation and usage guide
│
├── dashboard/                       # Web Dashboard (Flask)
│   ├── app.py                       # Flask application with WebSocket
│   ├── templates/
│   │   └── index.html               # Dashboard UI with checksum indicator
│   ├── static/
│   │   ├── style.css                # Premium responsive styling
│   │   └── script.js                # Real-time updates with Chart.js
│   ├── Dockerfile                   # Docker container for cloud deployment
│   ├── .env.example                 # Environment variable template
│   ├── HIVEMQ_SETUP.md             # HiveMQ Cloud setup guide
│   ├── requirements.txt             # Python dependencies
│   └── README.md                    # Deployment guide
│
├── ml-training/                     # ML Training Pipeline (Run on Laptop)
│   ├── train_model.py               # Train with RT-IoT2022 dataset (21 features)
│   ├── train_model_5features.py     # Train with 5 MQTT-specific features
│   ├── train_with_custom_data.py    # Train with YOUR collected data (recommended)
│   ├── implementation.py            # Research pipeline (paper reproduction)
│   ├── configs.py                   # ML configuration and feature lists
│   ├── utils.py                     # Utility functions
│   ├── models/                      # Trained models directory
│   │   ├── mqtt_ids_model.joblib   # Production model
│   │   └── model_results.csv        # Training metrics history
│   ├── data/                        # Training datasets
│   │   ├── RT_IOT2022.csv          # Public dataset (download separately)
│   │   ├── custom_benign_data.csv   # YOUR normal ESP32 traffic
│   │   └── custom_attack_data.csv   # YOUR attack simulations
│   └── README.md                    # Training documentation
│
├── docs/                            # Documentation
│   ├── DATA_INTEGRITY.md           # CRC32 checksum implementation guide
│   ├── RASPBERRY_PI_SETUP.md       # Raspberry Pi configuration
│
├── DEPLOYMENT.md                    # Cloud deployment guide
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

---

## 🚀 Quick Start

### Choose Your Architecture

This system supports **two deployment modes**:

| Mode | Best For | IP Blocking | Setup Complexity |
|------|----------|-------------|------------------|
| **Local** | Production, IP blocking, learning | ✅ Yes | Medium |
| **Cloud** | Remote access, quick demo | ❌ No | Easy |

---

## 🏠 **Local Setup** (Recommended for Production)

### Why Local?
- ✅ **IP blocking works** (Raspberry Pi sees actual device IPs)
- ✅ **Lower latency** (local network)
- ✅ **No cloud costs**
- ✅ **Better security** (data stays on-premises)
- ✅ **Custom ML training** (on YOUR traffic)

### Prerequisites

- **ESP32 Development Board** with DHT11/DHT22 sensor
- **Raspberry Pi 4** (1GB+ RAM recommended)
- **All devices on same WiFi network** (2.4GHz for ESP32)
- **Python 3.7+** on Raspberry Pi and laptop
- **Arduino IDE** with ESP32 support

---

### Step-by-Step Local Setup

#### 1️⃣ **Set Up Raspberry Pi Broker**

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Update system
sudo apt update && sudo apt upgrade -y

# Install Mosquitto MQTT broker
sudo apt install mosquitto mosquitto-clients -y

# Configure mosquitto for local connections
sudo nano /etc/mosquitto/mosquitto.conf
```

Add these lines:
```
listener 1883
allow_anonymous true
```

Restart mosquitto:
```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto

# Verify it's running
sudo systemctl status mosquitto
sudo netstat -tulpn | grep 1883
```

**Expected**: Port 1883 is listening

---

#### 2️⃣ **Set Up ESP32 Sensor**

```bash
# On your laptop
cd esp32-sensor

# Open main.ino in Arduino IDE
```

**Update these lines**:
```cpp
// WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_NAME";      // Your WiFi SSID
const char* WIFI_PASSWORD = "YOUR_PASSWORD";    // Your WiFi password

// MQTT Broker (Raspberry Pi)
const char* MQTT_BROKER = "raspberrypi.local";  // Or Pi's IP: "192.168.1.100"
const int MQTT_PORT = 1883;                     // Local port (no TLS)
const char* MQTT_USERNAME = "";                 // Empty for local
const char* MQTT_PASSWORD = "";  
```

**Upload to ESP32**:
1. Connect ESP32 via USB
2. Select Board: "ESP32 Dev Module"
3. Select Port: Your ESP32's COM port
4. Click Upload
5. Open Serial Monitor (115200 baud)

**Expected Output**:
```
=== ESP32 Secure MQTT Sensor Node ===
WiFi connected!
IP Address: 192.168.1.XXX
Connecting to MQTT broker... Connected!
✓ Published encrypted data (80 bytes) | Checksum: ABCD1234
```

**Detailed Instructions**: [esp32-sensor/README.md](esp32-sensor/README.md)

---

#### 3️⃣ **Collect Custom Training Data**

**IMPORTANT**: Skip the generic model, collect YOUR data!

**Copy data collection scripts to Raspberry Pi**:
```bash
# From your laptop
cd Mqtt_Encryption_Framework
scp raspberry-pi-gateway/collect_normal_data.py pi@raspberrypi.local:~/
scp raspberry-pi-gateway/collect_attack_data.py pi@raspberrypi.local:~/
```

**On Raspberry Pi, collect normal data** (with ESP32 running):
```bash
ssh pi@raspberrypi.local
python3 collect_normal_data.py --duration 600  # 10 minutes
```

**Collect attack data**:
```bash
python3 collect_attack_data.py --duration 1800  # 30 minutes
# Runs 4 attack types: flooding, large payloads, bursts, replay
```

**Copy data back to laptop**:
```bash
# On your laptop
scp pi@raspberrypi.local:~/custom_benign_data.csv ./ml-training/data/
scp pi@raspberrypi.local:~/custom_attack_data.csv ./ml-training/data/
```

---

#### 4️⃣ **Train Custom ML Model**

```bash
# On your laptop
cd ml-training

# Activate virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Clean attack data (remove false labels)
python clean_attack_data.py

# Train model on YOUR data
python train_with_custom_data.py --benign data/custom_benign_data.csv
```

**Expected Output**:
```
Cross-Validation F1 Scores: [0.9234, 0.9187, ...]
Mean CV F1: 0.9191

✓ Accuracy:  0.9985
✓ Model saved to: ./models/mqtt_ids_model.joblib
```

**Deploy model to Raspberry Pi**:
```bash
scp models/mqtt_ids_model.joblib pi@raspberrypi.local:~/ml-training/models/
```

---

#### 5️⃣ **Set Up Raspberry Pi IDS**

```bash
# Copy IDS script
scp raspberry-pi-gateway/live_ids.py pi@raspberrypi.local:~/
scp raspberry-pi-gateway/requirements.txt pi@raspberrypi.local:~/

# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Install Python dependencies
pip3 install -r requirements.txt

# Create ml-training directory structure
mkdir -p ~/ml-training/models

# Enable ML detection and IP blocking (edit live_ids.py)
nano ~/live_ids.py
```

**Set these flags** (around line 50-51):
```python
ENABLE_AUTO_BLOCK = True    # Enable automatic IP blocking
ENABLE_ML_DETECTION = True   # Enable ML-based attack detection
```

**Run IDS**:
```bash
sudo python3 live_ids.py
```

**Expected Output**:
```
============================================================
  RASPBERRY PI EDGE GATEWAY - INTRUSION DETECTION SYSTEM
============================================================

[✓] Model loaded successfully: DecisionTreeClassifier
[✓] Connected to MQTT broker at localhost:1883
[✓] Subscribed to topic: #
[✓] Checksum verification enabled
[*] IDS monitoring started...

[✓ NORMAL] Time: 2025-12-14 22:30:45 | Topic: home/sensor/data | Length: 80 bytes | Checksum: ✓
```

---

#### 6️⃣ **Set Up Dashboard**

```bash
# On your laptop
cd dashboard

# Create .env file
cp .env.example .env
nano .env
```

**Configure for local Raspberry Pi**:
```env
# Local Raspberry Pi Configuration
MQTT_BROKER=raspberrypi.local  # Or Pi's IP: 192.168.1.100
MQTT_PORT=1883
MQTT_USE_TLS=false
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=home/sensor/data
MQTT_CLIENT_ID=Dashboard_Client

FLASK_SECRET_KEY=mqtt-iot-dashboard-2024-secure-key
```

**Run dashboard**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app.py
```

**Access**: Open browser to **http://localhost:5000**

**Expected**: Live temperature/humidity data with green checksum indicator

---

### 🎯 Local Setup Verification

**Everything working when**:
- ✅ ESP32 publishes every 5 seconds (Serial Monitor)
- ✅ Raspberry Pi shows "[✓ NORMAL]" messages (NOT attacks)
- ✅ Dashboard shows live data with checksum ✓
- ✅ Charts update in real-time
- ✅ No false positives (normal traffic not flagged)

**Test IP Blocking**:
```bash
# Copy attack simulator to Raspberry Pi
scp raspberry-pi-gateway/attack_simulator.py pi@raspberrypi.local:~/

# On Raspberry Pi (new SSH session)
python3 attack_simulator.py --attack flood --duration 30

# IDS should show:
# [🚨 ATTACK DETECTED]
# [🔒 BLOCKED] IP address X.X.X.X

# Verify blocking:
sudo iptables -L INPUT -n
```

---

## ☁️ **Cloud Setup** (Quick Demo)

### Why Cloud?
- ✅ **Access from anywhere** (internet access)
- ✅ **Quick setup** (no local broker needed)
- ✅ **Managed service** (HiveMQ handles availability)
- ❌ **No IP blocking** (can't see device IPs)
- ❌ **Costs** (may hit free tier limits)

### Step-by-Step Cloud Setup

#### 1️⃣ **Set Up HiveMQ Cloud**

```bash
# 1. Go to: https://console.hivemq.cloud/
# 2. Create free account
# 3. Create a cluster (free tier: 100 connections, 10GB/month)
# 4. Note cluster URL: your-cluster.s1.eu.hivemq.cloud
# 5. Create credentials in "Access Management"
```

**Detailed Guide**: [dashboard/HIVEMQ_SETUP.md](dashboard/HIVEMQ_SETUP.md)

#### 2️⃣ **Configure ESP32 for Cloud**

```cpp
// In main.ino
const char* MQTT_BROKER = "your-cluster.s1.eu.hivemq.cloud";
const int MQTT_PORT = 8883;  // TLS port
const char* MQTT_USERNAME = "esp32_user";  // Your HiveMQ credentials
const char* MQTT_PASSWORD = "your_password";

// Use secure client
WiFiClientSecure espClient;
espClient.setInsecure();  // Skip cert validation for testing
```

#### 3️⃣ **Configure Dashboard for Cloud**

```env
# In dashboard/.env
MQTT_BROKER=your-cluster.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_USERNAME=dashboard_user
MQTT_PASSWORD=your_password
```

#### 4️⃣ **Optional: Configure Raspberry Pi for Cloud**

```python
# In live_ids.py
MQTT_BROKER = "your-cluster.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "ids_user"
MQTT_PASSWORD = "your_password"

# Add TLS (line ~438)
client.tls_set()
```

**Note**: IP blocking won't work in cloud mode (broker abstracts IPs)

---

## 🔄 **Switching Between Local ↔ Cloud**

### Local → Cloud

**ESP32**: Change broker to HiveMQ URL, port 8883, add credentials
**Dashboard**: Update `.env` with HiveMQ settings, set `MQTT_USE_TLS=true`
**Raspberry Pi**: Point to HiveMQ, add TLS, disable IP blocking

### Cloud → Local

**ESP32**: Change broker to `raspberrypi.local`, port 1883, remove credentials
**Dashboard**: Update `.env` to `raspberrypi.local`, set `MQTT_USE_TLS=false`
**Raspberry Pi**: Point to `localhost`, remove TLS, enable IP blocking

**Complete Config Guide**: `docs/configuration_sync_guide.md`

---

## 🏗️ System Architecture

```
┌─────────────────┐
│   ESP32 Sensor  │  ← Reads temperature/humidity
│   (C++/Arduino) │  ← Encrypts with AES-128
└────────┬────────┘  ← Publishes to MQTT
         │
         │ MQTT (Encrypted)
         ▼
┌─────────────────┐
│  Raspberry Pi   │  ← Subscribes to all MQTT traffic
│    Gateway      │  ← ML-based attack detection
│   (Python IDS)  │  ← Blocks malicious IPs (iptables)
└────────┬────────┘
         │
         │ MQTT Bridge / Port Forward
         ▼
┌─────────────────┐
│  Web Dashboard  │  ← Decrypts AES payloads
│   (Flask/Cloud) │  ← Real-time visualization
│                 │  ← WebSocket updates
└─────────────────┘
```

### Data Flow

1. **ESP32** reads DHT22 sensor → Creates JSON payload
2. **ESP32** calculates CRC32 checksum → Appends to payload
3. **ESP32** encrypts payload with AES-128 → Publishes to MQTT
4. **Raspberry Pi** receives encrypted packet → Extracts metadata
5. **Raspberry Pi** decrypts and verifies checksum → Detects corruption
6. **ML Model** analyzes packet metadata → Detects anomalies
7. **Firewall** blocks attacker IPs automatically (if enabled)
8. **Dashboard** subscribes to MQTT → Decrypts payload → Verifies checksum → Displays data


---

## 🧠 Machine Learning IDS

### ⚠️ Important: Custom Dataset Training Recommended

The system now supports **custom dataset collection** from YOUR actual ESP32 traffic, which dramatically improves accuracy and eliminates false positives.

### Two Training Approaches

#### Option 1: Quick Start (RT-IoT2022 Only) ❌ Not Recommended

**Problem**: Generic dataset doesn't match your ESP32's traffic patterns
- ESP32 sends data every 5 seconds
- RT-IoT2022 normal traffic has different timing
- Result: **100% false positive rate** (everything flagged as attack)

```bash
cd ml-training
python train_model_5features.py
```

**Use Case**: Initial testing only, not production

---

#### Option 2: Custom Dataset (YOUR Traffic) ✅ **Recommended**

**Solution**: Train on YOUR ESP32's actual traffic patterns

**Workflow**:

1. **Collect Normal Data** (10-30 minutes):
   ```bash
   # On Raspberry Pi
   python3 collect_normal_data.py --duration 600
   ```
   - Captures ESP32's 5-second intervals
   - Labels as benign (label=0)
   - Output: `custom_benign_data.csv`

2. **Collect Attack Data** (30 minutes):
   ```bash
   # On Raspberry Pi
   python3 collect_attack_data.py --duration 1800
   ```
   - Simulates: flooding, large payloads, bursts, replay attacks
   - Labels as malicious (label=1)
   - Output: `custom_attack_data.csv`

3. **Clean Attack Data** (remove false labels):
   ```bash
   # On your laptop
   cd ml-training
   python clean_attack_data.py
   ```

4. **Train Custom Model**:
   ```bash
   python train_with_custom_data.py --benign data/custom_benign_data.csv
   ```
   - Combines YOUR benign data + RT-IoT2022 attacks
   - Uses 5-fold cross-validation
   - Handles class imbalance
   - Output: `models/mqtt_ids_model.joblib`

5. **Deploy to Raspberry Pi**:
   ```bash
   scp models/mqtt_ids_model.joblib pi@raspberrypi.local:~/ml-training/models/
   ```

**Complete Guide**: See `docs/custom_model_workflow.md`

---

### Features Used (5 MQTT-Specific)

Optimized for MQTT packet metadata (no deep packet inspection needed):

1. **`flow_pkts_payload.max`** - Maximum packet size
2. **`flow_iat.std`** - Inter-arrival time (KEY: 5s normal, <0.1s attack)
3. **`flow_pkts_per_sec`** - Packet rate
4. **`payload_bytes_per_second`** - Throughput
5. **`flow_pkts_payload.tot`** - Total bytes

**Why 5 features?**
- Can be extracted from MQTT messages at runtime
- No need for network-layer packet inspection
- Faster inference
- Better generalization

---

### Performance Metrics

#### RT-IoT2022 Model (Generic):
- **Accuracy**: 99.98%
- **False Positive Rate on ESP32**: **100%** ❌
- **Usability**: Not suitable for production

#### Custom Model (YOUR Data):
- **Accuracy**: 99.85%
- **False Positive Rate on ESP32**: **0%** ✅
- **Cross-Validation F1**: 0.91-0.92
- **Usability**: Production-ready

**Key Insight**: Lower accuracy but ZERO false positives = much better!

---

### Attack Detection Capabilities

Custom model detects:
- **Flooding attacks** (>10 msg/sec)
- **Large payload attacks** (>1KB messages)
- **Burst attacks** (rapid bursts with pauses)
- **Replay attacks** (old timestamps, high frequency)
- **Topic injection** (unauthorized topics)

---

### Model Files

```bash
ml-training/models/
├── mqtt_ids_model.joblib           # Production model (5 features)
├── mqtt_ids_model_5features.joblib # RT-IoT2022 trained
├── mqtt_ids_model_custom.joblib    # Custom data trained
└── model_results.csv               # Training history
```

---

## ☁️ Cloud Deployment

### AWS EC2 (Free Tier)

```bash
# Launch t2.micro instance
# Install Docker and deploy dashboard
docker run -d -p 80:5000 mqtt-dashboard
```

### Google Cloud (Compute Engine)

```bash
# Create e2-micro instance
# Deploy with Cloud Run or Compute Engine
gcloud compute instances create mqtt-dashboard --machine-type=e2-micro
```

**Full Guide**: [dashboard/README.md - Cloud Deployment](dashboard/README.md)

---

## 🔧 Configuration

### Shared AES-128 Key

**IMPORTANT**: All three components must use the same key!

```python
# Python (Gateway & Dashboard)
AES_KEY = bytes([
    0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
    0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
])
```

```cpp
// C++ (ESP32)
unsigned char AES_KEY[16] = {
  0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
  0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
};
```

### MQTT Broker Configuration

**Option 1: HiveMQ Cloud** (Recommended):

All components connect to the same HiveMQ cluster:

```python
# ESP32 (main.ino)
const char* MQTT_BROKER = "your-cluster.s1.eu.hivemq.cloud";
const int MQTT_PORT = 8883;

# Dashboard (.env)
MQTT_BROKER=your-cluster.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USE_TLS=true

# Gateway (live_ids.py) - configure to connect to HiveMQ
MQTT_BROKER = "your-cluster.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
```

**Option 2: Local Mosquitto Broker**:

- **ESP32**: `MQTT_BROKER = "192.168.1.100"` (Raspberry Pi IP)
- **Gateway**: `MQTT_BROKER = "localhost"`
- **Dashboard**: `MQTT_BROKER = "192.168.1.100"` (or cloud IP)

---

## 📊 Features Summary

| Component | Features |
|-----------|----------|
| **ESP32** | DHT22 sensor reading, AES-128 encryption, CRC32 checksum generation, WiFi/MQTT connectivity |
| **Gateway** | ML intrusion detection, checksum verification, automatic IP blocking, attack logging |
| **Dashboard** | Real-time visualization, AES decryption, checksum validation, WebSocket updates, Docker support |


---

## 🐛 Troubleshooting

### ESP32 won't connect to WiFi

- Ensure 2.4GHz network (ESP32 doesn't support 5GHz)
- Check SSID and password are correct
- Verify signal strength (RSSI > -70 dBm)

### IDS not detecting attacks

- Ensure model file exists (`mqtt_ids_model.joblib`)
- Run `train_model.py` first
- Check MQTT broker is running

### Dashboard shows no data

- Verify MQTT broker IP is correct
- Check AES key matches ESP32 key
- Inspect browser console for errors

---

## 🔒 Security Best Practices

1. **Change Default Keys**: Never use the example AES key in production
2. **Enable MQTT TLS**: Use port 8883 with certificates
3. **Implement Authentication**: Use strong MQTT username/password
4. **Network Segmentation**: Isolate IoT devices on separate VLAN
5. **Regular Updates**: Keep firmware and software up-to-date
6. **Monitor Logs**: Review `ids_attack_log.txt` regularly

---

## 📚 Research Paper

This implementation is based on:

**"Enhancing MQTT Intrusion Detection in IoT Using Machine Learning and Feature Engineering"**

Key techniques:
- Pearson Correlation Coefficient (PCC) feature pruning
- Mutual Information (MI) ranking
- Euclidean distance feature engineering
- Decision Tree and k-NN classifiers

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is open-source and available under the MIT License.

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

---
