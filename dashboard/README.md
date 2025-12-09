# Dashboard - Secure MQTT IoT Visualizer

A beautiful, real-time web dashboard for visualizing encrypted IoT sensor data with AES-128 decryption.

## 🎯 Features

- **Real-time Updates**: WebSocket-based live data streaming
- **AES-128 Decryption**: Automatically decrypts encrypted MQTT payloads
- **Beautiful UI**: Premium dark theme with gradient animations
- **Interactive Charts**: Historical temperature and humidity trends
- **Responsive Design**: Works on desktop, tablet, and mobile
- **RESTful API**: JSON endpoints for data access

## 📋 Requirements

- **Python 3.7+**
- **MQTT Broker** (Mosquitto or cloud-based)
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**

```bash
cd dashboard
pip install -r requirements.txt
```

2. **Configure MQTT Broker**

Edit `app.py` and update:

```python
MQTT_BROKER = "192.168.1.100"  # Your Raspberry Pi IP or cloud broker
MQTT_PORT = 1883
MQTT_TOPIC = "home/sensor/data"
```

3. **Run the Dashboard**

```bash
python app.py
```

4. **Open in Browser**

Navigate to: `http://localhost:5000`

### 🐳 Docker Deployment

#### Build the Docker Image

```bash
docker build -t mqtt-dashboard .
```

#### Run the Container

```bash
docker run -d -p 5000:5000 --name mqtt-dashboard mqtt-dashboard
```

#### With Environment Variables

```bash
docker run -d -p 5000:5000 \
  -e MQTT_BROKER=your-broker-ip \
  --name mqtt-dashboard \
  mqtt-dashboard
```

## ☁️ Cloud Deployment

### AWS EC2 (Free Tier)

1. **Launch EC2 Instance**
   - AMI: Ubuntu Server 22.04 LTS
   - Instance Type: t2.micro (free tier)
   - Open port 5000 in Security Group

2. **Install Docker**

```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
```

3. **Deploy Container**

```bash
# Clone repository
git clone https://github.com/Harri200191/Mqtt_Encryption_Framework.git
cd Mqtt_Encryption_Framework/dashboard

# Build and run
sudo docker build -t mqtt-dashboard .
sudo docker run -d -p 5000:5000 --restart always mqtt-dashboard
```

4. **Access Dashboard**

Navigate to: `http://YOUR_EC2_PUBLIC_IP:5000`

### Google Cloud (Compute Engine)

1. **Create VM Instance**
   - Machine type: e2-micro (free tier)
   - Boot disk: Ubuntu 22.04 LTS
   - Firewall: Allow HTTP traffic

2. **SSH into Instance**

```bash
gcloud compute ssh your-instance-name
```

3. **Install and Deploy**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Deploy dashboard
git clone https://github.com/Harri200191/Mqtt_Encryption_Framework.git
cd Mqtt_Encryption_Framework/dashboard
sudo docker build -t mqtt-dashboard .
sudo docker run -d -p 80:5000 --restart always mqtt-dashboard
```

4. **Configure Firewall**

```bash
gcloud compute firewall-rules create allow-dashboard \
  --allow tcp:80 \
  --source-ranges 0.0.0.0/0 \
  --description "Allow dashboard access"
```

## 🔧 Configuration

### MQTT Settings

```python
MQTT_BROKER = "localhost"      # MQTT broker address
MQTT_PORT = 1883                # MQTT broker port
MQTT_TOPIC = "home/sensor/data" # Topic to subscribe to
MQTT_CLIENT_ID = "Dashboard_Client"
```

### AES Encryption Key

**IMPORTANT**: This must match the key on ESP32 and Raspberry Pi

```python
AES_KEY = bytes([
    0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
    0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
])
```

## 📡 API Endpoints

### GET `/api/latest`

Returns the latest sensor reading:

```json
{
  "temperature": 23.5,
  "humidity": 45.2,
  "sensor_id": "ESP32_Sensor_001",
  "timestamp": "2025-12-09 20:15:30",
  "status": "connected"
}
```

### GET `/api/history`

Returns historical readings (last 100):

```json
[
  {
    "temperature": 23.5,
    "humidity": 45.2,
    "timestamp": "2025-12-09 20:15:30"
  },
  ...
]
```

## 🌐 MQTT Bridging (Local to Cloud)

To connect local sensors to a cloud-hosted dashboard:

### Option 1: Mosquitto Bridge

Edit `/etc/mosquitto/mosquitto.conf` on Raspberry Pi:

```conf
connection bridge-to-cloud
address YOUR_CLOUD_IP:1883
topic home/sensor/data out 0
```

### Option 2: Port Forwarding

Forward router port 1883 to Raspberry Pi, then update dashboard MQTT_BROKER to your public IP.

**Security Warning**: Use VPN or certificate-based authentication for production!

## 🎨 UI Customization

The dashboard uses CSS custom properties for easy theming:

```css
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --bg-dark: #0f0f23;
    --bg-card: #1a1a2e;
}
```

Edit `static/style.css` to customize colors, fonts, and animations.

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No data appearing | Check MQTT broker connection and topic name |
| Decryption failed | Ensure AES_KEY matches ESP32 key exactly |
| WebSocket not connecting | Check firewall allows port 5000 |
| Charts not updating | Clear browser cache, check console for errors |

## 📊 Screenshot

The dashboard displays:
- 🌡️ Real-time temperature with trend indicators
- 💧 Real-time humidity with trend indicators
- 📡 Sensor status and connection info
- 📈 Interactive historical charts
- 🔒 AES-128 encryption indicator

## 🔒 Security Best Practices

1. **Change the AES key** from the default
2. **Use MQTT authentication** (username/password)
3. **Enable TLS/SSL** for MQTT connections
4. **Run behind reverse proxy** (nginx) in production
5. **Implement rate limiting** to prevent DoS attacks

## 📝 Notes

- WebSocket updates are instant (< 100ms latency)
- Historical data is stored in memory (resets on restart)
- For persistent storage, add database integration
- Charts display last 20 data points by default
