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
│   ├── main.ino                     # Main firmware code (with TLS support)
│   └── README.md                    # Setup and HiveMQ Cloud configuration
│
├── raspberry-pi-gateway/            # Raspberry Pi Edge Gateway (Python)
│   ├── live_ids.py                  # Real-time IDS with ML detection
│   ├── requirements.txt             # Python dependencies
│   └── README.md                    # Installation and usage guide
│
├── dashboard/                       # Web Dashboard (Flask)
│   ├── app.py                       # Flask application with env vars
│   ├── templates/
│   │   └── index.html               # Dashboard UI
│   ├── static/
│   │   ├── style.css                # Premium styling
│   │   └── script.js                # Real-time updates
│   ├── Dockerfile                   # Docker container
│   ├── .env.example                 # Environment variable template
│   ├── HIVEMQ_SETUP.md             # HiveMQ Cloud setup guide
│   ├── requirements.txt             # Python dependencies
│   └── README.md                    # Deployment guide
│
├── ml-training/                     # ML Training (Run on Laptop)
│   ├── train_model.py               # Production model training (exports .joblib)
│   ├── implementation.py            # Research pipeline (paper reproduction)
│   ├── configs.py                   # ML configuration
│   ├── utils.py                     # Utility functions
│   ├── models/                      # Trained models directory
│   │   └── mqtt_ids_model.joblib   # Exported model for gateway
│   └── README.md                    # Training documentation
│
├── docs/                            # Visual Assets
│   ├── system_architecture.png     # Architecture diagram
│   └── dashboard_preview.png       # Dashboard screenshot
│
├── DEPLOYMENT.md                    # Deployment guide (updated for HiveMQ)
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **ESP32 Development Board** with DHT22 sensor
- **Raspberry Pi 4** (2GB+ RAM recommended) - OR use HiveMQ Cloud
- **MQTT Broker**: HiveMQ Cloud (recommended, free tier) OR Mosquitto (local)
- **Python 3.7+**
- **Arduino IDE** with ESP32 support

### Step-by-Step Setup

#### 0️⃣ Set Up HiveMQ Cloud (Recommended)

```bash
# 1. Go to https://console.hivemq.cloud/
# 2. Create free account (100 connections, 10GB/month)
# 3. Create a cluster
# 4. Note your cluster URL (e.g., abc123.s1.eu.hivemq.cloud)
# 5. Create credentials in "Access Management"
```

**Benefits**: No local MQTT broker needed, works from anywhere!

See [dashboard/HIVEMQ_SETUP.md](dashboard/HIVEMQ_SETUP.md) for detailed guide.

#### 1️⃣ Set Up ESP32 Sensor

```bash
# Navigate to ESP32 folder
cd esp32-sensor

# Open main.ino in Arduino IDE
# Update WiFi credentials
# For HiveMQ: Change to WiFiClientSecure, port 8883, add credentials
# Upload to ESP32
```

**Detailed Instructions**: [esp32-sensor/README.md](esp32-sensor/README.md)

#### 2️⃣ Set Up Raspberry Pi Gateway (Optional if using HiveMQ)

```bash
# On Raspberry Pi
cd raspberry-pi-gateway

# Install dependencies
pip3 install -r requirements.txt

# Install Mosquitto broker (if not using HiveMQ)
sudo apt install mosquitto mosquitto-clients -y

# Train ML model (on laptop or Pi)
cd ../ml-training
python3 train_model.py

# Run IDS
cd ../raspberry-pi-gateway
sudo python3 live_ids.py
```

**Detailed Instructions**: [raspberry-pi-gateway/README.md](raspberry-pi-gateway/README.md)

#### 3️⃣ Set Up Dashboard

```bash
# Navigate to dashboard folder
cd dashboard

# Copy environment template
cp .env.example .env

# Edit .env with your HiveMQ credentials
nano .env

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# OR deploy with Docker
docker build -t mqtt-dashboard .
docker run -d -p 5000:5000 \
  -e MQTT_BROKER=your-cluster.s1.eu.hivemq.cloud \
  -e MQTT_PORT=8883 \
  -e MQTT_USE_TLS=true \
  -e MQTT_USERNAME=dashboard_user \
  -e MQTT_PASSWORD=your_password \
  mqtt-dashboard
```

**Detailed Instructions**: [dashboard/README.md](dashboard/README.md)

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
2. **ESP32** encrypts payload with AES-128 → Publishes to MQTT
3. **Raspberry Pi** receives encrypted packet → Extracts metadata
4. **ML Model** analyzes packet metadata → Detects anomalies
5. **Firewall** blocks attacker IPs automatically (if enabled)
6. **Dashboard** subscribes to MQTT → Decrypts payload → Displays data

---

## 🧠 Machine Learning IDS

### Dataset

Uses **RT-IoT2022** dataset with the following features:

- `active.avg`
- `bwd_bulk_packets`
- `bwd_data_pkts_tot`
- `flow_iat.max`
- `flow_pkts_per_sec`
- And 15 more network flow statistics...

### Model Training

```bash
cd raspberry-pi-gateway
python3 train_model.py
```

**Output**: `mqtt_ids_model.joblib` (Decision Tree classifier)

### Performance Metrics

Based on RT-IoT2022 dataset testing:

- **Accuracy**: ~99%
- **Precision**: ~98%
- **Recall**: ~99%
- **F1-Score**: ~98%

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
| **ESP32** | DHT22 sensor reading, AES-128 encryption, WiFi/MQTT connectivity |
| **Gateway** | ML intrusion detection, automatic IP blocking, attack logging |
| **Dashboard** | Real-time visualization, AES decryption, WebSocket updates, Docker support |

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

## 🎓 Academic Use

If using this project for academic research, please cite:

```
@misc{mqtt_encryption_framework,
  author = {Your Name},
  title = {Secure MQTT IoT System with ML-based Intrusion Detection},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/YOUR_USERNAME/Mqtt_Encryption_Framework}
}
```

---

## 🙏 Acknowledgments

- RT-IoT2022 dataset creators
- Arduino and ESP32 community
- Flask and Chart.js developers
- scikit-learn contributors

---

**Built with ❤️ for secure IoT systems**