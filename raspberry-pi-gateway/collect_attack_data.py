#!/usr/bin/env python3
"""
Generate and Collect Malicious MQTT Traffic Data

This script runs attack simulations while simultaneously collecting
the feature data, creating a custom "attack" dataset for training.

Usage:
    python3 collect_attack_data.py --duration 1800  # 30 minutes
"""

import paho.mqtt.client as mqtt
import time
import csv
import random
import string
import argparse
import threading
from datetime import datetime
from collections import defaultdict

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_ATTACKER_ID = "ATTACK_DATA_COLLECTOR"
MQTT_MONITOR_ID = "ATTACK_MONITOR"
MQTT_TOPIC = "#"  # Monitor all topics
OUTPUT_CSV = "./custom_attack_data.csv"

# Attack configuration
ATTACK_TOPICS = ["home/sensor/data", "test/attack", "malicious/topic"]

# Data collection
last_packet_time = {}
collected_data = []
attack_active = False

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
        'label': 1  # 1 = Attack/Malicious
    }

# ==================== MONITORING CLIENT ====================

def on_monitor_connect(client, userdata, flags, rc):
    """Callback when monitoring client connected"""
    if rc == 0:
        print(f"[✓] Monitor connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
        print(f"[✓] Monitoring all topics for attack data collection")
    else:
        print(f"[✗] Monitor connection failed with code {rc}")

def on_monitor_message(client, userdata, msg):
    """Callback when monitoring client receives a message"""
    global attack_active
    
    # Only collect data during active attacks
    if not attack_active:
        return
    
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
        
        # Add metadata
        features['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        features['topic'] = topic
        features['attack_type'] = userdata.get('current_attack', 'unknown')
        
        # Store
        collected_data.append(features)
        
        # Print progress (less verbose than benign collection)
        if len(collected_data) % 50 == 0:
            print(f"[{len(collected_data)}] Collected attack samples | "
                  f"Type: {features['attack_type']} | Rate: {features['flow_pkts_per_sec']:.1f}/s")
        
    except Exception as e:
        print(f"[✗] Error processing message: {e}")

# ==================== ATTACK PATTERNS ====================

class AttackGenerator:
    def __init__(self, broker, port):
        self.broker = broker
        self.port = port
        
        # Initialize attack client (paho-mqtt 2.0 compatible)
        try:
            self.client = mqtt.Client(client_id=MQTT_ATTACKER_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        except TypeError:
            self.client = mqtt.Client(MQTT_ATTACKER_ID)
        
        self.attack_count = 0
        self.connected = False
    
    def connect(self):
        """Connect to broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            self.connected = True
            print(f"[✓] Attacker connected as: {MQTT_ATTACKER_ID}")
            return True
        except Exception as e:
            print(f"[✗] Attacker connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
    
    def flooding_attack(self, duration, rate=100):
        """High-rate flooding attack"""
        global attack_active
        attack_active = True
        
        print(f"\n[🚨] Starting FLOODING attack ({rate} msg/sec for {duration}s)")
        
        topic = random.choice(ATTACK_TOPICS)
        start_time = time.time()
        
        while (time.time() - start_time) < duration and self.connected:
            payload = f'{{"temp":25.0,"attack":"flood","id":"{MQTT_ATTACKER_ID}"}}'
            self.client.publish(topic, payload)
            self.attack_count += 1
            time.sleep(1.0 / rate)
        
        attack_active = False
    
    def large_payload_attack(self, duration, size_kb=5):
        """Large payload attack"""
        global attack_active
        attack_active = True
        
        print(f"\n[🚨] Starting LARGE PAYLOAD attack ({size_kb}KB for {duration}s)")
        
        topic = random.choice(ATTACK_TOPICS)
        large_data = ''.join(random.choices(string.ascii_letters, k=size_kb*1024))
        payload = f'{{"data":"{large_data}","attack":"large"}}'
        
        start_time = time.time()
        
        while (time.time() - start_time) < duration and self.connected:
            self.client.publish(topic, payload)
            self.attack_count += 1
            time.sleep(1)  # One per second
        
        attack_active = False
    
    def burst_attack(self, duration, burst_size=50, burst_interval=5):
        """Burst attack - rapid bursts with pauses"""
        global attack_active
        attack_active = True
        
        print(f"\n[🚨] Starting BURST attack ({burst_size} msgs every {burst_interval}s for {duration}s)")
        
        topic = random.choice(ATTACK_TOPICS)
        start_time = time.time()
        
        while (time.time() - start_time) < duration and self.connected:
            # Send burst
            for _ in range(burst_size):
                payload = f'{{"attack":"burst","count":{self.attack_count}}}'
                self.client.publish(topic, payload)
                self.attack_count += 1
                time.sleep(0.01)  # 10ms between msgs in burst
            
            # Pause between bursts
            time.sleep(burst_interval)
        
        attack_active = False
    
    def replay_attack(self, duration, replay_rate=20):
        """Replay attack - resend old messages"""
        global attack_active
        attack_active = True
        
        print(f"\n[🚨] Starting REPLAY attack ({replay_rate} replays/sec for {duration}s)")
        
        topic = random.choice(ATTACK_TOPICS)
        old_msg = '{"temp":24.5,"hum":55.0,"timestamp":"2024-01-01 00:00:00"}'
        
        start_time = time.time()
        
        while (time.time() - start_time) < duration and self.connected:
            for _ in range(replay_rate):
                self.client.publish(topic, old_msg)
                self.attack_count += 1
            time.sleep(1)
        
        attack_active = False

# ==================== MAIN ====================

def save_to_csv():
    """Save collected attack data to CSV"""
    if not collected_data:
        print("\n[⚠] No attack data collected!")
        return
    
    print(f"\n[*] Saving {len(collected_data)} attack samples to {OUTPUT_CSV}...")
    
    fieldnames = [
        'timestamp',
        'topic',
        'attack_type',
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
    print("ATTACK DATA COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Attack samples collected: {len(collected_data)}")
    
    # Count by attack type
    attack_types = {}
    for row in collected_data:
        atype = row.get('attack_type', 'unknown')
        attack_types[atype] = attack_types.get(atype, 0) + 1
    
    print("\nSamples by attack type:")
    for atype, count in attack_types.items():
        print(f"  {atype}: {count}")
    
    print(f"\nOutput file: {OUTPUT_CSV}")
    print(f"\nNext steps:")
    print(f"1. Combine with benign data using train_with_custom_data.py")
    print(f"2. Train model with both benign and attack data")
    print(f"{'='*60}\n")

def run_attack_sequence(attacker, total_duration):
    """Run a sequence of different attacks for the specified duration"""
    
    # Calculate time per attack type (divide evenly)
    attack_types = 4
    time_per_attack = total_duration // attack_types
    
    print(f"\n{'='*60}")
    print(f"ATTACK SEQUENCE (Total: {total_duration}s = {total_duration/60:.1f} min)")
    print(f"{'='*60}")
    print(f"Each attack type: ~{time_per_attack}s ({time_per_attack/60:.1f} min)")
    print(f"{'='*60}\n")
    
    monitor_data = {'current_attack': 'flooding'}
    
    try:
        # 1. Flooding attack
        monitor_data['current_attack'] = 'flooding'
        attacker.flooding_attack(time_per_attack, rate=100)
        time.sleep(5)  # Short break between attacks
        
        # 2. Large payload attack
        monitor_data['current_attack'] = 'large_payload'
        attacker.large_payload_attack(time_per_attack, size_kb=5)
        time.sleep(5)
        
        # 3. Burst attack
        monitor_data['current_attack'] = 'burst'
        attacker.burst_attack(time_per_attack, burst_size=50, burst_interval=3)
        time.sleep(5)
        
        # 4. Replay attack
        monitor_data['current_attack'] = 'replay'
        attacker.replay_attack(time_per_attack, replay_rate=20)
        
    except KeyboardInterrupt:
        print("\n[*] Attack sequence interrupted by user")

def main():
    global OUTPUT_CSV
    
    parser = argparse.ArgumentParser(description='Generate and collect malicious MQTT traffic data')
    parser.add_argument('--duration', type=int, default=1800,
                       help='Total duration in seconds (default: 1800 = 30 min)')
    parser.add_argument('--output', type=str, default=OUTPUT_CSV,
                       help='Output CSV file path')
    
    args = parser.parse_args()
    OUTPUT_CSV = args.output
    
    print("\n" + "="*60)
    print("  MALICIOUS MQTT TRAFFIC DATA COLLECTION")
    print("="*60 + "\n")
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Duration: {args.duration} seconds ({args.duration/60:.1f} minutes)")
    print(f"Output: {OUTPUT_CSV}")
    print("\n⚠️  This will generate attack traffic on your MQTT broker!")
    print("⚠️  Make sure this is acceptable for your environment.\n")
    
    # Initialize monitoring client
    try:
        monitor_client = mqtt.Client(client_id=MQTT_MONITOR_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    except TypeError:
        monitor_client = mqtt.Client(MQTT_MONITOR_ID)
    
    monitor_client.on_connect = on_monitor_connect
    monitor_client.on_message = on_monitor_message
    monitor_client.user_data_set({'current_attack': 'none'})
    
    try:
        print("[*] Starting monitoring client...")
        monitor_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        monitor_client.loop_start()
        time.sleep(2)  # Wait for connection
        
        # Initialize attack generator
        print("[*] Starting attack generator...")
        attacker = AttackGenerator(MQTT_BROKER, MQTT_PORT)
        
        if not attacker.connect():
            print("[✗] Failed to connect attacker")
            return
        
        time.sleep(2)
        
        # Run attack sequence
        run_attack_sequence(attacker, args.duration)
        
        # Cleanup
        print("\n[*] Stopping attack generator...")
        attacker.disconnect()
        
        print("[*] Stopping monitor...")
        monitor_client.loop_stop()
        monitor_client.disconnect()
        
        # Save collected data
        save_to_csv()
        
    except Exception as e:
        print(f"[✗] Error: {e}")
    finally:
        try:
            monitor_client.loop_stop()
            monitor_client.disconnect()
        except:
            pass

if __name__ == "__main__":
    main()
