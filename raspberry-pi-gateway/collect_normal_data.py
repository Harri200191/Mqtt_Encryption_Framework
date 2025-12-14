#!/usr/bin/env python3
"""
Collect Normal MQTT Traffic Data from ESP32

This script monitors MQTT traffic from your ESP32 and extracts features
to build a custom "benign" dataset that represents YOUR normal traffic.

Usage:
    python3 collect_normal_data.py --duration 600  # Collect for 10 minutes
"""

import paho.mqtt.client as mqtt
import time
import csv
import argparse
from datetime import datetime
from collections import defaultdict

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "#"  # Subscribe to all topics
OUTPUT_CSV = "./custom_benign_data.csv"

# Data collection
packet_history = defaultdict(list)
last_packet_time = {}
collected_data = []

def extract_features(topic, payload_length, time_delta):
    """Extract 5 features matching our model"""
    packets_per_sec = 1.0 / (time_delta + 0.001)
    bytes_per_sec = payload_length / (time_delta + 0.001)
    
    return {
        'flow_pkts_payload.max': payload_length,
        'flow_iat.std': time_delta,
        'flow_pkts_per_sec': packets_per_sec,
        'payload_bytes_per_second': bytes_per_sec,
        'flow_pkts_payload.tot': payload_length,
        'label': 0  # 0 = Benign/Normal
    }

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"[✓] Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"[✓] Subscribed to topic: {MQTT_TOPIC}")
        print(f"[*] Collecting data to: {OUTPUT_CSV}")
        print("[*] Monitoring started...\n")
    else:
        print(f"[✗] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback when a message is received"""
    try:
        timestamp = time.time()
        topic = msg.topic
        payload_length = len(msg.payload)
        
        # Calculate time delta
        if topic in last_packet_time:
            time_delta = timestamp - last_packet_time[topic]
        else:
            time_delta = 0
        
        last_packet_time[topic] = timestamp
        
        # Extract features
        features = extract_features(topic, payload_length, time_delta)
        
        # Add timestamp and topic for reference
        features['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        features['topic'] = topic
        
        # Store
        collected_data.append(features)
        
        # Print progress
        print(f"[{len(collected_data)}] Topic: {topic} | Size: {payload_length}B | "
              f"Delta: {time_delta:.3f}s | Rate: {features['flow_pkts_per_sec']:.2f}/s")
        
    except Exception as e:
        print(f"[✗] Error processing message: {e}")

def save_to_csv(duration):
    """Save collected data to CSV"""
    if not collected_data:
        print("\n[⚠] No data collected!")
        return
    
    print(f"\n[*] Saving {len(collected_data)} samples to {OUTPUT_CSV}...")
    
    # Define CSV columns (matching RT-IoT2022 feature names)
    fieldnames = [
        'timestamp',
        'topic',
        'flow_pkts_payload.max',
        'flow_iat.std',
        'flow_pkts_per_sec',
        'payload_bytes_per_second',
        'flow_pkts_payload.tot',
        'label'
    ]
    
    with open(OUTPUT_CSV, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(collected_data)
    
    print(f"[✓] Data saved successfully!")
    print(f"\n{'='*60}")
    print("COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Duration: {duration} seconds")
    print(f"Samples collected: {len(collected_data)}")
    print(f"Average packet rate: {len(collected_data)/duration:.2f} packets/sec")
    print(f"Output file: {OUTPUT_CSV}")
    print(f"\nNext steps:")
    print(f"1. Review {OUTPUT_CSV} to verify all data is normal/benign")
    print(f"2. Use train_with_custom_data.py to train model with this data")
    print(f"{'='*60}\n")

def main():
    global OUTPUT_CSV  # Declare global at the start
    
    parser = argparse.ArgumentParser(description='Collect normal MQTT traffic data')
    parser.add_argument('--duration', type=int, default=600,
                       help='Duration to collect data in seconds (default: 600 = 10 min)')
    parser.add_argument('--output', type=str, default=OUTPUT_CSV,
                       help='Output CSV file path')
    
    args = parser.parse_args()
    
    OUTPUT_CSV = args.output
    
    print("\n" + "="*60)
    print("  NORMAL MQTT TRAFFIC DATA COLLECTION")
    print("="*60 + "\n")
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Duration: {args.duration} seconds ({args.duration/60:.1f} minutes)")
    print(f"Output: {OUTPUT_CSV}\n")
    
    # Initialize MQTT client (paho-mqtt 2.0 compatible)
    try:
        # Try paho-mqtt 2.0+ API
        client = mqtt.Client(client_id="Data_Collector", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    except TypeError:
        # Fall back to paho-mqtt 1.x API
        client = mqtt.Client("Data_Collector")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Collect for specified duration
        start_time = time.time()
        try:
            while (time.time() - start_time) < args.duration:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Collection interrupted by user")
        
        client.loop_stop()
        client.disconnect()
        
        # Save data
        save_to_csv(args.duration)
        
    except Exception as e:
        print(f"[✗] Error: {e}")

if __name__ == "__main__":
    main()
