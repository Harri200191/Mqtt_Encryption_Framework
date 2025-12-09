
 🚀 Deployment Guide
Complete step-by-step deployment instructions for the Secure MQTT IoT System across all three components.
---
## 📋 Pre-Deployment Checklist
Before beginning deployment, ensure you have:
- [ ] ESP32 development board with DHT22 sensor
- [ ] Raspberry Pi 4 with Raspberry Pi OS installed
- [ ] AWS or GCP account (for cloud dashboard)
- [ ] RT-IoT2022 dataset downloaded
- [ ] Network connectivity between all components
---
## 🔧 Part 1: ESP32 Sensor Node
### Hardware Setup
1. **Connect DHT22 Sensor to ESP32**:
   ```
   DHT22 VCC  → ESP32 3.3V
   DHT22 DATA → ESP32 GPIO 4
   DHT22 GND  → ESP32 GND
   ```
2. **Add 10kΩ pull-up resistor** between VCC and DATA
### Software Setup
1. **Install Arduino IDE**:
   - Download from https://www.arduino.cc/en/software
   - Install ESP32 board package
2. **Install Required Libraries**:
   - PubSubClient
   - DHT sensor library
   - Adafruit Unified Sensor
3. **Configure Credentials**:
   Open `esp32-sensor/main.ino` and update:
   **For Local MQTT Broker (Raspberry Pi)**:
   
   ```cpp
   const char* WIFI_SSID = "YourWiFiName";
   const char* WIFI_PASSWORD = "YourWiFiPassword";
   const char* MQTT_BROKER = "192.168.1.100";  // Raspberry Pi IP
   const int MQTT_PORT = 1883;
   ```
   **For HiveMQ Cloud** (Recommended for Production):
   
   ```cpp
   #include <WiFiClientSecure.h>  // Add this line
   
   const char* WIFI_SSID = "YourWiFiName";
   const char* WIFI_PASSWORD = "YourWiFiPassword";
   const char* MQTT_BROKER = "your-cluster.s1.eu.hivemq.cloud";  // HiveMQ cluster URL
   const int MQTT_PORT = 8883;  // TLS port
   const char* MQTT_USERNAME = "esp32_user";
   const char* MQTT_PASSWORD = "your_password";
   
   // In global section, change:
   WiFiClientSecure espClient;  // Instead of WiFiClient
   
   // In setup(), add:
   espClient.setInsecure();  // Skip cert validation (testing only)
   ```
   See [esp32-sensor/README.md](esp32-sensor/README.md) for detailed HiveMQ setup.
4. **Upload Firmware**:
   - Select Board: `ESP32 Dev Module`
   - Select Port: Your COM port
   - Click Upload
5. **Verify Operation**:
   - Open Serial Monitor (115200 baud)
   - Should see WiFi connection and MQTT publishing
### Troubleshooting
- **WiFi won't connect**: Use 2.4GHz network only
- **Upload fails**: Hold BOOT button during upload
- **Sensor reads NaN**: Check wiring and pull-up resistor
- **MQTT connection rc=-2**: Check broker URL and WiFi
- **MQTT connection rc=5**: Wrong username/password (HiveMQ)
---
## 🛡️ Part 2: Raspberry Pi Gateway
### Initial Setup
1. **Update System**:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```
2. **Install Mosquitto MQTT Broker**:
   ```bash
   sudo apt install mosquitto mosquitto-clients -y
   sudo systemctl enable mosquitto
   sudo systemctl start mosquitto
   ```
3. **Verify Mosquitto**:
   ```bash
   mosquitto -v
   # Should show version and running status
   ```
### Install Python Dependencies
```bash
cd ~/Mqtt_Encryption_Framework/raspberry-pi-gateway
pip3 install -r requirements.txt
```
### Train ML Model
1. **Download RT-IoT2022 Dataset**:
   - Place in `../data/RT_IOT2022.csv`
   - Place in `../ml-training/data/RT_IOT2022.csv`
2. **Run Training Script**:
2. **Run Training Script** (On your laptop or Raspberry Pi):
   ```bash
   cd ../ml-training
   python3 train_model.py
   ```
   This creates `mqtt_ids_model.joblib`
   This creates `models/mqtt_ids_model.joblib`
3. **Model is ready** for use by the gateway
### Configure MQTT Broker
**Option A: Local Mosquitto** (Default):
```python
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
```
**Option B: HiveMQ Cloud**:
Edit `live_ids.py`:
```python
MQTT_BROKER = "your-cluster.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "gateway_user"
MQTT_PASSWORD = "your_password"
# Add TLS support (requires paho-mqtt with TLS)
client.tls_set()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
```
### Run IDS
```bash
sudo python3 live_ids.py
```
**Note**: Requires `sudo` for iptables firewall control
### Auto-Start on Boot
Create systemd service:
```bash
sudo nano /etc/systemd/system/mqtt-ids.service
```
Add content:
```ini
[Unit]
Description=MQTT IDS Gateway
After=network.target mosquitto.service
[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/Mqtt_Encryption_Framework/raspberry-pi-gateway
ExecStart=/usr/bin/python3 live_ids.py
Restart=always
[Install]
WantedBy=multi-user.target
```
Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mqtt-ids
sudo systemctl start mqtt-ids
```
### Verify Operation
```bash
# Check service status
sudo systemctl status mqtt-ids
# View logs
sudo journalctl -u mqtt-ids -f
# Test MQTT
mosquitto_sub -t "#" -v
```
---
## 🖥️ Part 3: Web Dashboard
### Configuration
The dashboard uses environment variables for configuration. Create a `.env` file:
```bash
cd ~/Mqtt_Encryption_Framework/dashboard
cp .env.example .env
nano .env
```
**For Local MQTT Broker**:
```env
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USE_TLS=false
MQTT_USERNAME=
MQTT_PASSWORD=
```
**For HiveMQ Cloud** (Recommended):
```env
MQTT_BROKER=your-cluster.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_USERNAME=dashboard_user
MQTT_PASSWORD=your_password
```
See [dashboard/HIVEMQ_SETUP.md](dashboard/HIVEMQ_SETUP.md) for detailed setup.
### Local Deployment
```bash
# Build image
docker build -t mqtt-dashboard .
# Run container
# Run with environment variables
docker run -d \
  --name mqtt-dashboard \
  -p 5000:5000 \
  -e MQTT_BROKER=your-cluster.s1.eu.hivemq.cloud \
  -e MQTT_PORT=8883 \
  -e MQTT_USE_TLS=true \
  -e MQTT_USERNAME=dashboard_user \
  -e MQTT_PASSWORD=your_password \
  --restart unless-stopped \
  mqtt-dashboard
```
---
## ☁️ Cloud Deployment Options
### Option 0: HiveMQ Cloud MQTT Broker (Recommended First Step)
Before deploying to AWS or GCP, consider using **HiveMQ Cloud** as your MQTT broker:
**Benefits**:
- ✅ No need to manage your own MQTT broker
- ✅ Free tier: 100 connections, 10GB/month
- ✅ Global CDN, low latency
- ✅ Built-in TLS/SSL security
- ✅ No IP address changes or port forwarding needed
**Setup**:
1. Go to https://console.hivemq.cloud/
2. Create free account and cluster
3 Follow [dashboard/HIVEMQ_SETUP.md](dashboard/HIVEMQ_SETUP.md)
4. Configure all components (ESP32, Gateway, Dashboard) to use HiveMQ URL
**Result**: All devices connect to HiveMQ Cloud, dashboard can be anywhere!
---
### Option A: AWS EC2 Free Tier
**1. Launch EC2 Instance**:
- AMI: Ubuntu Server 22.04 LTS
- Instance Type: `t2.micro` (free tier eligible)
- Storage: 8GB gp2
- Security Group: Allow TCP 5000 (or 80)
**2. Connect via SSH**:
```bash
ssh -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com
```
**3. Install Docker**:
```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```
**4. Deploy Dashboard**:
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Mqtt_Encryption_Framework.git
cd Mqtt_Encryption_Framework/dashboard
# Build and run
docker build -t mqtt-dashboard .
docker run -d -p 80:5000 --restart always mqtt-dashboard
```
**5. Configure MQTT Broker Connection**:
Edit `app.py` before building:
```python
MQTT_BROKER = "YOUR_RASPBERRY_PI_PUBLIC_IP"
```
Or use MQTT bridge (see below).
**6. Access Dashboard**:
Navigate to: `http://YOUR_EC2_PUBLIC_IP`
---
### Option B: Google Cloud Compute Engine
**1. Create VM Instance**:
```bash
gcloud compute instances create mqtt-dashboard \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=10GB \
  --tags=http-server
```
**2. SSH into Instance**:
```bash
gcloud compute ssh mqtt-dashboard
```
**3. Install Docker**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```
**4. Deploy Dashboard**:
```bash
git clone https://github.com/YOUR_USERNAME/Mqtt_Encryption_Framework.git
cd Mqtt_Encryption_Framework/dashboard
docker build -t mqtt-dashboard .
docker run -d -p 80:5000 --restart always mqtt-dashboard
```
**5. Configure Firewall**:
```bash
gcloud compute firewall-rules create allow-dashboard \
  --allow tcp:80 \
  --target-tags http-server
```
**6. Get External IP**:
```bash
gcloud compute instances describe mqtt-dashboard \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```
---
## 🌉 MQTT Bridging (Local to Cloud)
To connect local ESP32/Raspberry Pi to cloud-hosted dashboard:
### Method 1: Mosquitto Bridge
On Raspberry Pi, edit `/etc/mosquitto/mosquitto.conf`:
```conf
# Local listener
listener 1883
allow_anonymous true
# Bridge to cloud
connection bridge-to-cloud
address YOUR_CLOUD_IP:1883
topic home/sensor/data out 0
topic # both 0
bridge_attempt_unsubscribe false
bridge_protocol_version mqttv311
```
Restart Mosquitto:
```bash
sudo systemctl restart mosquitto
```
### Method 2: Port Forwarding
1. **Configure Router**:
   - Forward external port 1883 → Raspberry Pi IP:1883
2. **Update Dashboard**:
   ```python
   MQTT_BROKER = "YOUR_PUBLIC_IP"
   ```
**⚠️ Security Warning**: Use TLS/SSL in production!
### Method 3: VPN Tunnel (Most Secure)
1. **Set up WireGuard or OpenVPN** between Raspberry Pi and cloud
2. Use VPN internal IPs for MQTT communication
---
## 🔐 Security Hardening
### 1. Enable MQTT Authentication
Edit `/etc/mosquitto/mosquitto.conf`:
```conf
allow_anonymous false
password_file /etc/mosquitto/passwd
```
Create password file:
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd mqtt_user
sudo systemctl restart mosquitto
```
Update clients with credentials.
### 2. Enable TLS/SSL
Generate certificates:
```bash
cd /etc/mosquitto/certs
sudo openssl req -new -x509 -days 365 -extensions v3_ca \
  -keyout ca.key -out ca.crt
```
Configure Mosquitto for TLS (port 8883).
### 3. Change Default AES Key
Generate a new random key:
```python
import os
key = os.urandom(16)
print([hex(b) for b in key])
```
Update in all three components.
### 4. Firewall Rules
On Raspberry Pi:
```bash
sudo ufw allow 1883/tcp  # MQTT
sudo ufw allow 22/tcp    # SSH
sudo ufw enable
```
---
## 📊 Monitoring & Maintenance
### Check ESP32 Status
- Serial monitor shows connection status
- MQTT publish success messages
### Monitor Raspberry Pi IDS
```bash
# View live logs
sudo journalctl -u mqtt-ids -f
# View attack log
tail -f ~/Mqtt_Encryption_Framework/raspberry-pi-gateway/ids_attack_log.txt
# Check blocked IPs
sudo iptables -L INPUT -n | grep DROP
```
### Dashboard Health Check
```bash
# Check if container is running
docker ps
# View logs
docker logs mqtt-dashboard
# Restart if needed
docker restart mqtt-dashboard
```
---
## 🧪 Testing the System
### 1. Test ESP32 Publishing
Use MQTT client to verify:
```bash
mosquitto_sub -h RASPBERRY_PI_IP -t "home/sensor/data" -v
```
You should see encrypted binary data.
### 2. Test IDS Detection
Send abnormal MQTT traffic and check IDS logs for detections.
### 3. Test Dashboard
Navigate to dashboard URL and verify:
- Real-time data updates
- Charts populate
- WebSocket connection active
---
## 🐛 Common Issues
| Issue | Solution |
|-------|----------|
| ESP32 can't connect to broker | Check Raspberry Pi IP, ensure Mosquitto is running |
| IDS shows "Model not found" | Run `train_model.py` first |
| Dashboard shows no data | Verify MQTT broker IP and AES key match |
| Permission denied (iptables) | Run IDS with `sudo` |
| Cloud dashboard can't reach local broker | Set up MQTT bridge or VPN |
---
## 📈 Scaling Considerations
For production deployments:
- **Multiple Sensors**: Update ESP32 CLIENT_ID to be unique
- **Load Balancing**: Use MQTT cluster or cloud broker (HiveMQ, AWS IoT)
- **Database**: Add PostgreSQL/TimescaleDB for persistent storage
- **High Availability**: Deploy dashboard on Kubernetes
- **Monitoring**: Add Prometheus + Grafana
---
## ✅ Deployment Verification
Once deployed, verify:
- [ ] ESP32 connects to WiFi and MQTT
- [ ] ESP32 publishes encrypted data every 5 seconds
- [ ] Raspberry Pi IDS detects and logs traffic
- [ ] Dashboard displays real-time temperature/humidity
- [ ] Charts update with new data
- [ ] Attack detection triggers IP blocking (if enabled)
---
## 🎉 Success!
Your Secure MQTT IoT System is now deployed! 
**Next Steps**:
- Monitor attack logs regularly
- Tune ML model threshold as needed
- Add more sensors by cloning ESP32 code
- Implement persistent database for historical data
- Add email/SMS alerts for detected attacks
---
**Need Help?** Open an issue on GitHub or consult component-specific READMEs.