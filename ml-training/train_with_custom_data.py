#!/usr/bin/env python3
"""
Train ML Model with Custom Benign Data + Custom Attack Data

This script uses 100% YOUR collected data (benign + attack) to train
a model tailored to YOUR ESP32's traffic patterns.

Usage:
    python3 train_with_custom_data.py --benign data/custom_benign_data.csv --attack data/custom_attack_data.csv
"""

import sys
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
import argparse

def train_with_custom_data(custom_benign_csv, custom_attack_csv, use_cross_validation=True):
    """Train model with 100% custom data - both benign and attack"""
    
    print("\n" + "="*60)
    print("  CUSTOM MQTT IDS MODEL TRAINING (100% Your Data)")
    print("="*60 + "\n")
    
    # 1. Load custom benign data
    print("[1/6] Loading custom benign data...")
    try:
        df_benign = pd.read_csv(custom_benign_csv)
        print(f"      Benign dataset shape: {df_benign.shape}")
    except FileNotFoundError:
        print(f"[✗] Benign dataset not found: {custom_benign_csv}")
        print("    Run: python3 collect_normal_data.py --duration 600")
        return
    
    # 2. Load custom attack data
    print("[2/6] Loading custom attack data...")
    try:
        df_attack = pd.read_csv(custom_attack_csv)
        print(f"      Attack dataset shape: {df_attack.shape}")
    except FileNotFoundError:
        print(f"[✗] Attack dataset not found: {custom_attack_csv}")
        print("    Run: python3 collect_attack_data.py --duration 1800")
        return
    
    # 3. Select the 5 MQTT features
    print("[3/6] Preparing features...")
    
    feature_cols = [
        'flow_pkts_payload.max',
        'flow_iat.std',
        'flow_pkts_per_sec',
        'payload_bytes_per_second',
        'flow_pkts_payload.tot'
    ]
    
    # Verify features exist
    for col in feature_cols:
        if col not in df_benign.columns:
            print(f"[✗] Missing feature in benign data: {col}")
            return
        if col not in df_attack.columns:
            print(f"[✗] Missing feature in attack data: {col}")
            return
    
    # Extract features and labels
    X_benign = df_benign[feature_cols].copy()
    y_benign = df_benign['label'].values if 'label' in df_benign.columns else np.zeros(len(X_benign))
    
    X_attack = df_attack[feature_cols].copy()
    y_attack = df_attack['label'].values if 'label' in df_attack.columns else np.ones(len(X_attack))
    
    print(f"      Benign samples: {len(X_benign)}")
    print(f"      Attack samples: {len(X_attack)}")
    
    # 4. Combine datasets
    print("[4/6] Combining datasets...")
    X = pd.concat([X_benign, X_attack], ignore_index=True)
    y = np.concatenate([y_benign, y_attack])
    
    # Convert to numeric and handle missing values
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(0)
    
    print(f"      Total samples: {len(X)}")
    print(f"      Benign: {sum(y==0)} ({sum(y==0)/len(y)*100:.1f}%)")
    print(f"      Attacks: {sum(y==1)} ({sum(y==1)/len(y)*100:.1f}%)")
    
    # Show feature statistics
    print(f"\n      Feature statistics:")
    print(f"      Benign mean inter-arrival time: {X_benign['flow_iat.std'].mean():.2f}s")
    print(f"      Attack mean inter-arrival time: {X_attack['flow_iat.std'].mean():.2f}s")
    print(f"      Benign mean packet rate: {X_benign['flow_pkts_per_sec'].mean():.2f} pkt/s")
    print(f"      Attack mean packet rate: {X_attack['flow_pkts_per_sec'].mean():.2f} pkt/s")
    
    # 5. Train model
    print("\n[5/6] Training model...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if use_cross_validation:
        # Use 5-fold cross-validation
        print("      Using 5-fold cross-validation...")
        model = DecisionTreeClassifier(
            random_state=42,
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight='balanced'
        )
        
        # Cross-validation scores
        cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='f1_weighted')
        print(f"\n      Cross-Validation F1 Scores: {cv_scores}")
        print(f"      Mean CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"      Train samples: {len(X_train)}")
    print(f"      Test samples: {len(X_test)}")
    
    # Train final model
    model = DecisionTreeClassifier(
        random_state=42,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)
    
    # 6. Evaluate
    print("\n[6/6] Evaluating model...")
    y_pred = model.predict(X_test)
    
    print("\n" + "="*60)
    print("MODEL EVALUATION")
    print("="*60)
    print(classification_report(y_test, y_pred, target_names=['Normal (ESP32)', 'Attack']))
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    print(f"\n✓ Accuracy:  {accuracy:.4f}")
    print(f"✓ Precision: {precision:.4f}")
    print(f"✓ Recall:    {recall:.4f}")
    print(f"✓ F1-Score:  {f1:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE")
    print("="*60)
    print(feature_importance.to_string(index=False))
    print("\nKey: flow_iat.std (inter-arrival time) should be most important")
    print("     ESP32 normal = ~5s, attacks = <0.5s")
    
    # Save results
    results_data = {
        'timestamp': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
        'model': ['DecisionTree_100PercentCustom'],
        'accuracy': [accuracy],
        'precision': [precision],
        'recall': [recall],
        'f1_score': [f1],
        'num_features': [5],
        'features': [','.join(feature_cols)],
        'benign_samples': [sum(y==0)],
        'attack_samples': [sum(y==1)],
        'train_samples': [len(X_train)],
        'test_samples': [len(X_test)]
    }
    
    results_df = pd.DataFrame(results_data)
    results_csv_path = './models/model_results.csv'
    
    try:
        existing_results = pd.read_csv(results_csv_path)
        results_df = pd.concat([existing_results, results_df], ignore_index=True)
    except FileNotFoundError:
        pass
    
    results_df.to_csv(results_csv_path, index=False)
    print(f"\n[✓] Results saved to: {results_csv_path}")
    
    # Export model
    print("\n[*] Exporting model...")
    model_data = {
        'model': model,
        'scaler': scaler,
        'features': feature_cols,
        'training_date': pd.Timestamp.now().isoformat(),
        'data_source': '100% Custom (Benign + Attack)',
        'benign_samples': sum(y==0),
        'attack_samples': sum(y==1),
        'performance': {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    }
    
    output_path = './models/mqtt_ids_model_custom.joblib'
    joblib.dump(model_data, output_path)
    print(f"[✓] Model saved to: {output_path}")
    
    # Also save as default name
    default_path = './models/mqtt_ids_model.joblib'
    joblib.dump(model_data, default_path)
    print(f"[✓] Model also saved to: {default_path}")
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print("\nYour model is now trained on YOUR traffic patterns:")
    print(f"  ✓ Knows ESP32 normal = ~5 second intervals")
    print(f"  ✓ Knows attacks = high rate, bursts, large payloads")
    print(f"  ✓ Zero reliance on RT-IoT2022 dataset")
    print(f"\nNext steps:")
    print(f"1. Copy model to Raspberry Pi:")
    print(f"   scp models/mqtt_ids_model.joblib pi@raspberrypi.local:~/ml-training/models/")
    print(f"2. Enable ML detection in live_ids.py:")
    print(f"   Set ENABLE_ML_DETECTION = True")
    print(f"3. Enable IP blocking:")
    print(f"   Set ENABLE_AUTO_BLOCK = True")
    print(f"4. Restart IDS: sudo python3 ~/live_ids.py")
    print(f"5. Test with: python3 attack_simulator.py --attack flood --duration 30")

def main():
    parser = argparse.ArgumentParser(description='Train model with 100% custom data')
    parser.add_argument('--benign', type=str, default='./data/custom_benign_data.csv',
                       help='Path to custom benign data CSV file')
    parser.add_argument('--attack', type=str, default='./data/custom_attack_data.csv',
                       help='Path to custom attack data CSV file')
    parser.add_argument('--no-cv', action='store_true',
                       help='Skip cross-validation (faster training)')
    
    args = parser.parse_args()
    
    train_with_custom_data(args.benign, args.attack, use_cross_validation=not args.no_cv)

if __name__ == "__main__":
    main()
