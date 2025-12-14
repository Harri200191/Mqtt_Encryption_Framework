#!/usr/bin/env python3
"""
Augment Benign Data

Creates synthetic variations of your benign ESP32 data to balance the dataset.
Uses realistic noise and variations based on sensor behavior.

Usage:
    python augment_benign_data.py --input data/custom_benign_data.csv --multiplier 100
"""

import pandas as pd
import numpy as np
import argparse

def augment_benign_data(input_csv, output_csv, multiplier=100):
    """
    Augment benign data by adding realistic variations
    
    Args:
        input_csv: Path to original benign data
        output_csv: Path to save augmented data
        multiplier: How many times to multiply the data (default: 100x)
    """
    
    print("\n" + "="*60)
    print("  BENIGN DATA AUGMENTATION")
    print("="*60 + "\n")
    
    # Load original data
    print(f"[1/4] Loading original benign data...")
    df_original = pd.read_csv(input_csv)
    original_count = len(df_original)
    print(f"      Original samples: {original_count}")
    
    # Features to augment
    feature_cols = [
        'flow_pkts_payload.max',
        'flow_iat.std',
        'flow_pkts_per_sec',
        'payload_bytes_per_second',
        'flow_pkts_payload.tot'
    ]
    
    # Calculate statistics for realistic variations
    print(f"\n[2/4] Analyzing feature distributions...")
    stats = {}
    for col in feature_cols:
        stats[col] = {
            'mean': df_original[col].mean(),
            'std': df_original[col].std(),
            'min': df_original[col].min(),
            'max': df_original[col].max()
        }
        print(f"      {col}:")
        print(f"        Mean: {stats[col]['mean']:.4f}, Std: {stats[col]['std']:.4f}")
    
    # Generate augmented data
    print(f"\n[3/4] Generating {multiplier}x augmented samples...")
    augmented_rows = []
    
    for _ in range(multiplier):
        for idx, row in df_original.iterrows():
            new_row = row.copy()
            
            # Add realistic Gaussian noise to each feature
            for col in feature_cols:
                if col == 'flow_iat.std':
                    # Inter-arrival time: add small jitter (±5% of mean)
                    # ESP32's 5-second interval can vary slightly
                    noise_std = stats[col]['std'] * 0.05
                    noise = np.random.normal(0, noise_std)
                    new_row[col] = max(4.5, min(5.5, row[col] + noise))  # Keep in realistic range
                
                elif col == 'flow_pkts_payload.max' or col == 'flow_pkts_payload.tot':
                    # Payload size: can vary by ±2 bytes (sensor readings fluctuate)
                    noise = np.random.randint(-2, 3)
                    new_row[col] = max(60, min(70, row[col] + noise))  # Typical MQTT payload range
                
                elif col == 'flow_pkts_per_sec':
                    # Packet rate: derived from inter-arrival time
                    new_row[col] = 1.0 / new_row['flow_iat.std']
                
                elif col == 'payload_bytes_per_second':
                    # Throughput: derived from payload size and rate
                    new_row[col] = new_row['flow_pkts_payload.max'] / new_row['flow_iat.std']
            
            # Keep timestamp and topic from original (or generate new)
            if 'timestamp' in new_row:
                # Optionally randomize timestamp slightly
                pass
            
            # Ensure label remains 0 (benign)
            new_row['label'] = 0
            
            augmented_rows.append(new_row)
    
    # Combine original + augmented
    df_augmented = pd.DataFrame(augmented_rows)
    df_combined = pd.concat([df_original, df_augmented], ignore_index=True)
    
    print(f"      Generated {len(augmented_rows)} augmented samples")
    print(f"      Total benign samples: {len(df_combined)}")
    
    # Save
    print(f"\n[4/4] Saving augmented data...")
    df_combined.to_csv(output_csv, index=False)
    
    print(f"\n{'='*60}")
    print("AUGMENTATION COMPLETE!")
    print(f"{'='*60}")
    print(f"Original samples:   {original_count}")
    print(f"Augmented samples:  {len(augmented_rows)}")
    print(f"Total samples:      {len(df_combined)} ({multiplier + 1}x increase)")
    print(f"Output file:        {output_csv}")
    print(f"\nNext steps:")
    print(f"1. Train model with augmented data:")
    print(f"   python train_with_custom_data.py --benign {output_csv}")
    print(f"2. Check class balance is better (~50/50 ideally)")

def main():
    parser = argparse.ArgumentParser(description='Augment benign data with synthetic variations')
    parser.add_argument('--input', type=str, default='./data/custom_benign_data.csv',
                       help='Input benign CSV file')
    parser.add_argument('--output', type=str, default='./data/custom_benign_data_augmented.csv',
                       help='Output CSV file for augmented data')
    parser.add_argument('--multiplier', type=int, default=100,
                       help='How many times to multiply the data (default: 100)')
    
    args = parser.parse_args()
    
    augment_benign_data(args.input, args.output, args.multiplier)

if __name__ == "__main__":
    main()
