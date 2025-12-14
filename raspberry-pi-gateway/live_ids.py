#!/usr/bin/env python3
"""
Raspberry Pi Edge Gateway - Intrusion Detection System (IDS)

This script acts as the central security hub for the IoT network.
It monitors all MQTT traffic, uses a trained ML model to detect attacks,
and automatically blocks malicious sources using iptables firewall rules.

Features:
- Real-time MQTT traffic monitoring
- ML-based intrusion detection (Decision Tree / kNN)
- Automatic IP blocking via iptables
- Attack logging and alerting
- Traffic metadata extraction

Requirements:
- Python 3.7+
- Trained model file: mqtt_ids_model.joblib
- Root/sudo access for iptables commands
- Mosquitto broker running locally
"""

import json
import time
import sys
import subprocess
from datetime import datetime
from collections import defaultdict
import numpy as np
import joblib
import paho.mqtt.client as mqtt
import zlib  # For CRC32 checksum verification
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ==================== CONFIGURATION ====================

# MQTT Broker Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "RaspberryPi_IDS_Gateway"
MQTT_USERNAME = None   # HiveMQ Cloud authentication
MQTT_PASSWORD = None   # HiveMQ Cloud authentication
SUBSCRIBE_TOPIC = "#"  # Subscribe to all topics

# ML Model Configuration
MODEL_PATH = "./../ml-training/models/mqtt_ids_model.joblib"

# IDS Settings
DETECTION_THRESHOLD = 0.5  # Confidence threshold for attack detection
ENABLE_AUTO_BLOCK = True    # Automatically block detected attackers
ATTACK_LOG_FILE = "./ids_attack_log.txt"
ENABLE_CHECKSUM_VERIFICATION = True  # Verify data integrity using checksums

# AES Encryption Key (MUST match ESP32 and dashboard)
AES_KEY = bytes([
    0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
    0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
])

# Feature Extraction Settings
PACKET_WINDOW_SIZE = 10  # Number of packets to track for feature extraction

# ==================== GLOBAL VARIABLES ====================

ml_model = None
scaler = None
packet_history = defaultdict(list)
blocked_ips = set()
last_packet_time = {}
packet_stats = {
    "total_packets": 0,
    "attacks_detected": 0,
    "ips_blocked": 0,
    "checksum_failures": 0
}

# ==================== MQTT CALLBACKS ====================

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"[✓] Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(SUBSCRIBE_TOPIC)
        print(f"[✓] Subscribed to topic: {SUBSCRIBE_TOPIC}")
        if ENABLE_CHECKSUM_VERIFICATION:
            print("[✓] Checksum verification enabled")
        print("[*] IDS monitoring started...\n")
    else:
        print(f"[✗] Connection failed with code {rc}")
        sys.exit(1)

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
        Decrypted string or None
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
            return data_with_checksum, None
        
        parts = data_with_checksum.rsplit('|', 1)
        data = parts[0]
        received_checksum = parts[1].strip()
        
        # Calculate expected checksum
        calculated_checksum = calculate_crc32(data)
        
        # Verify
        is_valid = (received_checksum == calculated_checksum)
        
        return data, is_valid
        
    except Exception as e:
        return data_with_checksum, False

def on_message(client, userdata, msg):
    """Callback when a message is received"""
    try:
        # Extract packet metadata
        timestamp = time.time()
        topic = msg.topic
        payload = msg.payload
        payload_length = len(payload)
        
        # Try to decrypt and verify checksum if enabled
        checksum_valid = None
        if ENABLE_CHECKSUM_VERIFICATION:
            try:
                decrypted_data = decrypt_aes(payload)
                if decrypted_data:
                    _, checksum_valid = verify_checksum(decrypted_data)
                    if checksum_valid is False:
                        packet_stats["checksum_failures"] += 1
                        print(f"[⚠ CHECKSUM FAILURE] Topic: {topic} | Length: {payload_length} bytes")
            except:
                pass  # Continue with IDS analysis even if decryption fails
        
        # Calculate time delta from last packet
        if topic in last_packet_time:
            time_delta = timestamp - last_packet_time[topic]
        else:
            time_delta = 0
        
        last_packet_time[topic] = timestamp
        
        # Extract features for ML model
        features = extract_features(topic, payload_length, time_delta)
        
        # Perform intrusion detection
        is_attack, confidence = detect_intrusion(features)
        
        packet_stats["total_packets"] += 1
        
        # Log packet info
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if is_attack:
            packet_stats["attacks_detected"] += 1
            print(f"[🚨 ATTACK DETECTED] Time: {timestamp_str}")
            print(f"    Topic: {topic}")
            print(f"    Payload Length: {payload_length} bytes")
            print(f"    Confidence: {confidence:.2%}")
            if checksum_valid is not None:
                print(f"    Checksum: {'VALID' if checksum_valid else 'INVALID'}")
            
            # Extract source IP (if available)
            # In a real scenario, you'd extract this from network layer
            source_ip = extract_source_ip(msg)
            
            if source_ip and ENABLE_AUTO_BLOCK:
                block_ip(source_ip)
            
            # Log attack
            log_attack(timestamp_str, topic, payload_length, source_ip, confidence)
            print()
        else:
            checksum_indicator = ""
            if checksum_valid is True:
                checksum_indicator = " | Checksum: ✓"
            elif checksum_valid is False:
                checksum_indicator = " | Checksum: ✗"
            print(f"[✓ NORMAL] Time: {timestamp_str} | Topic: {topic} | Length: {payload_length} bytes{checksum_indicator}")
        
    except Exception as e:
        print(f"[✗] Error processing message: {e}")

# ==================== FEATURE EXTRACTION ====================

def extract_features(topic, payload_length, time_delta):
    """
    Extract features from MQTT packet metadata for ML model
    
    The features are designed to mimic network flow statistics
    used in the RT-IoT2022 dataset training.
    
    Returns:
        numpy array of features
    """
    features = {
        "packet_length": payload_length,
        "time_delta": time_delta,
        "topic_length": len(topic),
        "packets_per_sec": 1.0 / (time_delta + 0.001),  # Avoid division by zero
        "avg_payload_size": payload_length,
        # Add more engineered features as needed
    }
    
    # Convert to numpy array in the order expected by the model
    # IMPORTANT: Match the feature order used during training
    feature_vector = np.array([
        features["packet_length"],
        features["time_delta"],
        features["topic_length"],
        features["packets_per_sec"],
        features["avg_payload_size"],
    ])
    
    return feature_vector.reshape(1, -1)

# ==================== INTRUSION DETECTION ====================

def detect_intrusion(features):
    """
    Use ML model to detect if packet is malicious
    
    Args:
        features: Numpy array of extracted features
        
    Returns:
        (is_attack, confidence): Tuple of boolean and float
    """
    if ml_model is None:
        return False, 0.0
    
    try:
        # Scale features if scaler is available
        if scaler is not None:
            features = scaler.transform(features)
        
        # Get prediction
        prediction = ml_model.predict(features)[0]
        
        # Get confidence (if model supports predict_proba)
        try:
            probabilities = ml_model.predict_proba(features)[0]
            confidence = probabilities[prediction]
        except:
            confidence = 1.0 if prediction == 1 else 0.0
        
        is_attack = (prediction == 1) and (confidence >= DETECTION_THRESHOLD)
        
        return is_attack, confidence
        
    except Exception as e:
        print(f"[✗] Model prediction error: {e}")
        return False, 0.0

# ==================== FIREWALL MANAGEMENT ====================

def block_ip(ip_address):
    """
    Block an IP address using iptables firewall
    
    Args:
        ip_address: IP address to block
    """
    if ip_address in blocked_ips:
        print(f"[⚠] IP {ip_address} is already blocked")
        return
    
    try:
        # Execute iptables command to drop packets from the IP
        command = f"sudo iptables -A INPUT -s {ip_address} -j DROP"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            blocked_ips.add(ip_address)
            packet_stats["ips_blocked"] += 1
            print(f"[🔒 BLOCKED] IP address {ip_address} has been blocked via iptables")
        else:
            print(f"[✗] Failed to block IP {ip_address}: {result.stderr}")
            
    except Exception as e:
        print(f"[✗] Error blocking IP: {e}")

def unblock_ip(ip_address):
    """
    Unblock a previously blocked IP address
    
    Args:
        ip_address: IP address to unblock
    """
    try:
        command = f"sudo iptables -D INPUT -s {ip_address} -j DROP"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            blocked_ips.discard(ip_address)
            print(f"[🔓 UNBLOCKED] IP address {ip_address} has been unblocked")
        else:
            print(f"[✗] Failed to unblock IP {ip_address}: {result.stderr}")
            
    except Exception as e:
        print(f"[✗] Error unblocking IP: {e}")

def list_blocked_ips():
    """Display all currently blocked IPs"""
    if blocked_ips:
        print("\n[🔒 Blocked IPs]")
        for ip in blocked_ips:
            print(f"  - {ip}")
    else:
        print("\n[ℹ] No IPs are currently blocked")

# ==================== UTILITIES ====================

def extract_source_ip(msg):
    """
    Extract source IP from MQTT message metadata
    
    In a production environment, this would extract the actual client IP
    from the broker's connection metadata or from application-layer headers.
    
    For this demo, we'll return a placeholder.
    """
    # TODO: Implement actual IP extraction logic
    # This could involve broker plugins, custom MQTT properties, or network sniffing
    return None  # Return None for now

def log_attack(timestamp, topic, payload_length, source_ip, confidence):
    """Log attack details to file"""
    try:
        with open(ATTACK_LOG_FILE, "a") as f:
            log_entry = f"{timestamp} | ATTACK | Topic: {topic} | Length: {payload_length} | IP: {source_ip} | Confidence: {confidence:.2%}\n"
            f.write(log_entry)
    except Exception as e:
        print(f"[✗] Failed to write to log file: {e}")

def print_statistics():
    """Print IDS statistics"""
    print("\n" + "="*50)
    print("IDS STATISTICS")
    print("="*50)
    print(f"Total Packets Analyzed: {packet_stats['total_packets']}")
    print(f"Attacks Detected: {packet_stats['attacks_detected']}")
    print(f"Checksum Failures: {packet_stats['checksum_failures']}")
    print(f"IPs Blocked: {packet_stats['ips_blocked']}")
    if packet_stats['total_packets'] > 0:
        attack_rate = (packet_stats['attacks_detected'] / packet_stats['total_packets']) * 100
        print(f"Attack Rate: {attack_rate:.2f}%")
    print("="*50 + "\n")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function to start the IDS"""
    global ml_model, scaler
    
    print("\n" + "="*60)
    print("  RASPBERRY PI EDGE GATEWAY - INTRUSION DETECTION SYSTEM")
    print("="*60 + "\n")
    
    # Load ML model
    print(f"[*] Loading ML model from {MODEL_PATH}...")
    try:
        model_data = joblib.load(MODEL_PATH)
        
        # Handle different model storage formats
        if isinstance(model_data, dict):
            ml_model = model_data.get("model")
            scaler = model_data.get("scaler")
        else:
            ml_model = model_data
            scaler = None
        
        print(f"[✓] Model loaded successfully: {type(ml_model).__name__}")
        
    except FileNotFoundError:
        print(f"[✗] Model file not found: {MODEL_PATH}")
        print("[!] Running in DEMO mode without ML detection")
        ml_model = None
    except Exception as e:
        print(f"[✗] Failed to load model: {e}")
        print("[!] Running in DEMO mode without ML detection")
        ml_model = None
    
    # Initialize MQTT client
    print(f"\n[*] Initializing MQTT client...")
    # Fix for paho-mqtt 2.0+ compatibility
    try:
        # Try paho-mqtt 2.0+ API (with callback_api_version)
        client = mqtt.Client(client_id=MQTT_CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    except TypeError:
        # Fall back to paho-mqtt 1.x API (without callback_api_version)
        client = mqtt.Client(MQTT_CLIENT_ID)
    
    # # Configure TLS for HiveMQ Cloud (port 8883)
    # client.tls_set()
    # print("[🔒] TLS/SSL encryption enabled")
    
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        print(f"[🔑] Authentication configured for user: {MQTT_USERNAME}")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Connect to broker
    try:
        print(f"[*] Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"[✗] Failed to connect to MQTT broker: {e}")
        sys.exit(1)
    
    # Start monitoring loop
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\n[*] Shutting down IDS...")
        print_statistics()
        list_blocked_ips()
        client.disconnect()
        print("[✓] Shutdown complete")

# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    main()
