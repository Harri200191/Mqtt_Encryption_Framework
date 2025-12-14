#!/usr/bin/env python3
"""
MQTT IoT Dashboard - Flask Web Application

This dashboard subscribes to encrypted MQTT sensor data,
decrypts it using AES-128, and displays real-time temperature
and humidity readings in a beautiful web interface.

Features:
- Real-time sensor data visualization
- AES-128 decryption
- WebSocket updates for live data
- Responsive web design
- Historical data charts
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import json
import threading
from datetime import datetime
from collections import deque
import zlib  # For CRC32 checksum verification

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# ==================== CONFIGURATION ====================

import os

# Flask Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'mqtt-iot-dashboard-2024-secure-key')
socketio = SocketIO(app, cors_allowed_origins="*")

# MQTT Configuration (Load from environment variables)
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'home/sensor/data')
MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'Dashboard_Client')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')  # Optional for cloud brokers
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')  # Optional for cloud brokers
MQTT_USE_TLS = os.getenv('MQTT_USE_TLS', 'false').lower() == 'true'  # Enable for cloud brokers

# AES Encryption Key (MUST match ESP32 and gateway)
AES_KEY = bytes([
    0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
    0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
])

# ==================== GLOBAL DATA ====================

# Store recent sensor readings (max 100 entries)
sensor_data_history = deque(maxlen=100)
latest_sensor_data = {
    "temperature": None,
    "humidity": None,
    "sensor_id": None,
    "timestamp": None,
    "status": "waiting",
    "checksum_valid": None
}

# ==================== MQTT FUNCTIONS ====================

def calculate_crc32(data):
    """
    Calculate CRC32 checksum for data integrity verification
    
    Args:
        data: String or bytes data
        
    Returns:
        CRC32 checksum as hex string (uppercase)
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return format(zlib.crc32(data) & 0xFFFFFFFF, '08X')

def decrypt_aes(ciphertext):
    """
    Decrypt AES-128 ECB encrypted data
    
    Args:
        ciphertext: Encrypted bytes
        
    Returns:
        Decrypted string with checksum (format: data|CHECKSUM)
    """
    try:
        cipher = AES.new(AES_KEY, AES.MODE_ECB)
        decrypted = cipher.decrypt(ciphertext)
        
        # Remove padding
        try:
            unpadded = unpad(decrypted, AES.block_size)
        except:
            # Manual padding removal (zeros)
            unpadded = decrypted.rstrip(b'\x00')
        
        return unpadded.decode('utf-8')
    except Exception as e:
        print(f"[✗] Decryption error: {e}")
        return None

def verify_checksum(data_with_checksum):
    """
    Verify checksum and extract data
    
    Args:
        data_with_checksum: String in format "data|CHECKSUM"
        
    Returns:
        Tuple of (data, is_valid)
    """
    try:
        # Split data and checksum
        if '|' not in data_with_checksum:
            print("[⚠] No checksum found in data")
            return data_with_checksum, None
        
        parts = data_with_checksum.rsplit('|', 1)
        data = parts[0]
        received_checksum = parts[1].strip()
        
        # Calculate expected checksum
        calculated_checksum = calculate_crc32(data)
        
        # Verify
        is_valid = (received_checksum == calculated_checksum)
        
        if is_valid:
            print(f"[✓] Checksum valid: {received_checksum}")
        else:
            print(f"[✗] Checksum MISMATCH! Received: {received_checksum}, Calculated: {calculated_checksum}")
        
        return data, is_valid
        
    except Exception as e:
        print(f"[✗] Checksum verification error: {e}")
        return data_with_checksum, False

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"[✓] Dashboard connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
        print(f"[✓] Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"[✗] Connection failed with code {rc}")

def on_mqtt_message(client, userdata, msg):
    """Callback when MQTT message is received"""
    try:
        # Decrypt the payload
        decrypted_data = decrypt_aes(msg.payload)
        
        if decrypted_data:
            # Verify checksum and extract data
            data_str, checksum_valid = verify_checksum(decrypted_data)
            
            # Parse JSON
            data = json.loads(data_str)
            
            # Extract sensor readings
            temperature = data.get('temp')
            humidity = data.get('hum')
            sensor_id = data.get('id', 'Unknown')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update latest data
            latest_sensor_data.update({
                "temperature": temperature,
                "humidity": humidity,
                "sensor_id": sensor_id,
                "timestamp": timestamp,
                "status": "connected" if checksum_valid else "checksum_error",
                "checksum_valid": checksum_valid
            })
            
            # Add to history (only if checksum is valid)
            if checksum_valid:
                sensor_data_history.append({
                    "timestamp": timestamp,
                    "temperature": temperature,
                    "humidity": humidity
                })
            
            # Broadcast to all connected clients via WebSocket
            socketio.emit('sensor_update', latest_sensor_data)
            
            checksum_status = "✓" if checksum_valid else "✗ CHECKSUM FAILED"
            print(f"[📊] {checksum_status} | Temp: {temperature}°C | Humidity: {humidity}% | ID: {sensor_id}")
            
    except json.JSONDecodeError as e:
        print(f"[✗] JSON decode error: {e}")
    except Exception as e:
        print(f"[✗] Message processing error: {e}")

def start_mqtt_client():
    """Initialize and start MQTT client in background thread"""
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    # Configure TLS if enabled (for cloud brokers like HiveMQ)
    # if MQTT_USE_TLS:
    #     mqtt_client.tls_set()
    #     print("[🔒] TLS/SSL encryption enabled")
    
    # Set credentials if provided (for cloud brokers)
    if MQTT_USERNAME and MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        print(f"[🔑] Authentication enabled for user: {MQTT_USERNAME}")
    
    try:
        print(f"[*] Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"[✗] MQTT connection error: {e}")

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('index.html')

@app.route('/api/latest')
def get_latest_data():
    """API endpoint to get latest sensor data"""
    return jsonify(latest_sensor_data)

@app.route('/api/history')
def get_history():
    """API endpoint to get historical sensor data"""
    return jsonify(list(sensor_data_history))

# ==================== SOCKETIO EVENTS ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"[✓] Client connected")
    # Send latest data immediately
    emit('sensor_update', latest_sensor_data)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"[ℹ] Client disconnected")

# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  MQTT IOT DASHBOARD - Starting Server")
    print("="*60 + "\n")
    
    # Start MQTT client in background thread
    mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()
    print("[*] MQTT client thread started\n")
    
    # Start Flask web server
    print("[*] Starting Flask web server...")
    print("[*] Dashboard will be available at: http://localhost:5000")
    print("[*] Press Ctrl+C to stop\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
