# Raspberry Pi Edge Gateway

This component acts as the **central security hub** for your IoT network. It runs a Machine Learning-based Intrusion Detection System (IDS) and controls the firewall to block malicious traffic.

## 🎯 Features

- **Real-time MQTT Traffic Monitoring**: Subscribes to all MQTT topics
- **ML-based Attack Detection**: Uses trained Decision Tree model
- **Automatic IP Blocking**: Blocks attackers via iptables firewall
- **Attack Logging**: Maintains detailed logs of detected attacks
- **Statistics Dashboard**: Real-time monitoring statistics

## 📋 Requirements

### Hardware
- **Raspberry Pi 4** (2GB+ RAM recommended)
- **MicroSD Card** (16GB+ with Raspberry Pi OS)
- **Stable Internet Connection**

### Software
- **Python 3.7+**
- **Mosquitto MQTT Broker** (installed locally)
- **Root/sudo access** (for iptables firewall control)

## 🔧 Installation

### 1. Install Mosquitto MQTT Broker

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients -y
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### 2. Install Python Dependencies

```bash
cd raspberry-pi-gateway
pip3 install -r requirements.txt
```

### 3. Transfer Pre-trained Model

The ML model should be trained on your laptop (see `ml-training/` folder) and then transferred to the Raspberry Pi.

**Transfer the model file:**

```bash
# Method 1: SCP (Secure Copy) - Recommended
scp mqtt_ids_model.joblib pi@raspberrypi.local:~/raspberry-pi-gateway/

# Method 2: USB Drive
# Copy mqtt_ids_model.joblib to USB → Transfer to Pi

# Method 3: Git (if model is committed)
# On Pi: git pull
```

**Verify the model exists:**
```bash
ls -lh ~/raspberry-pi-gateway/mqtt_ids_model.joblib
```

---

### 4. Run the IDS

```bash
sudo python3 live_ids.py
```

**Note:** `sudo` is required for iptables firewall control.

### Expected Output

```
============================================================
  RASPBERRY PI EDGE GATEWAY - INTRUSION DETECTION SYSTEM
============================================================

[*] Loading ML model from ./mqtt_ids_model.joblib...
[✓] Model loaded successfully: DecisionTreeClassifier

[*] Initializing MQTT client...
[*] Connecting to MQTT broker at localhost:1883...
[✓] Connected to MQTT broker at localhost:1883
[✓] Subscribed to topic: #
[*] IDS monitoring started...

[✓ NORMAL] Time: 2025-12-09 20:15:23 | Topic: home/sensor/data | Length: 64 bytes
[✓ NORMAL] Time: 2025-12-09 20:15:28 | Topic: home/sensor/data | Length: 64 bytes
[🚨 ATTACK DETECTED] Time: 2025-12-09 20:15:35
    Topic: home/sensor/data
    Payload Length: 512 bytes
    Confidence: 87.50%
[🔒 BLOCKED] IP address 192.168.1.150 has been blocked via iptables
```

## ⚙️ Configuration

Edit the constants in `live_ids.py`:

```python
# MQTT Settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# IDS Settings
DETECTION_THRESHOLD = 0.5  # Confidence threshold (0.0 - 1.0)
ENABLE_AUTO_BLOCK = True    # Auto-block attackers
ATTACK_LOG_FILE = "./ids_attack_log.txt"
```

## 🔒 Firewall Management

### View Blocked IPs

```bash
sudo iptables -L INPUT -n | grep DROP
```

### Manually Block an IP

```bash
sudo iptables -A INPUT -s 192.168.1.100 -j DROP
```

### Manually Unblock an IP

```bash
sudo iptables -D INPUT -s 192.168.1.100 -j DROP
```

### Clear All Firewall Rules

```bash
sudo iptables -F INPUT
```

## 📊 Monitoring

### View Attack Logs

```bash
tail -f ids_attack_log.txt
```

### Check Mosquitto Logs

```bash
sudo tail -f /var/log/mosquitto/mosquitto.log
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Model file not found | Run `train_model.py` first to create the model |
| Permission denied (iptables) | Run script with `sudo` |
| MQTT connection failed | Ensure Mosquitto is running: `sudo systemctl status mosquitto` |
| All traffic flagged as attack | Retrain model or adjust `DETECTION_THRESHOLD` |

## 🔄 Auto-Start on Boot (Optional)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/mqtt-ids.service
```

Add this content:

```ini
[Unit]
Description=MQTT IDS Gateway
After=network.target mosquitto.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/raspberry-pi-gateway
ExecStart=/usr/bin/python3 /home/pi/raspberry-pi-gateway/live_ids.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mqtt-ids
sudo systemctl start mqtt-ids
```

## 📝 Notes

- The IDS analyzes packet metadata (length, timing, topic) to detect anomalies
- Feature extraction mimics network flow statistics from RT-IoT2022 dataset
- IP blocking persists until reboot unless firewall rules are saved
- For production, implement persistent iptables rules using `iptables-persistent`

## 🎓 Model Information

The ML model is trained on:
- **Dataset**: RT-IoT2022
- **Algorithm**: Decision Tree Classifier
- **Features**: 21 selected features + engineered euclidean distance
- **Performance**: ~99% accuracy on test set (paper results)
