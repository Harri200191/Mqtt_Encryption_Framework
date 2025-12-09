#!/usr/bin/env python3
"""
Train and export the ML model for the IDS

This script uses the existing implementation.py to train a model
and exports it in a format ready for live_ids.py to use.
"""

import sys
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report

from configs import *
from utils import *

def train_and_export_model():
    """Train the IDS model and export it for production use"""
    
    print("\n" + "="*60)
    print("  MQTT IDS MODEL TRAINING")
    print("="*60 + "\n")
    
    # 1. Load data
    print("[1/7] Loading dataset...")
    try:
        df = pd.read_csv(DATA_PATH)
        print(f"      Dataset shape: {df.shape}")
    except FileNotFoundError:
        print(f"[✗] Dataset not found at {DATA_PATH}")
        print("    Please download the RT-IoT2022 dataset")
        return
    
    # 2. Prepare labels
    print("[2/7] Preparing labels...")
    label_col = find_label_column(df)
    y = binary_encode_labels(df[label_col])
    print(f"      Label distribution: {pd.Series(y).value_counts().to_dict()}")
    
    # 3. Prepare features
    print("[3/7] Preparing features...")
    for col in ['service', 'proto']:
        if col in df.columns:
            df = df.drop(columns=[col])
    
    X = df.drop(columns=[label_col]).copy()
    
    # Convert to numeric
    for c in X.select_dtypes(include=['object']).columns:
        try:
            X[c] = pd.to_numeric(X[c])
        except:
            X = X.drop(columns=[c])
    
    # Drop constant columns
    const_cols = X.columns[X.nunique() <= 1].tolist()
    if const_cols:
        X = X.drop(columns=const_cols)
    
    # 4. Feature selection
    print("[4/7] Performing feature selection...")
    if FEATURES_LIST is not None:
        selected_cols = [f for f in FEATURES_LIST if f in X.columns]
    else:
        # Use correlation + mutual information
        from sklearn.feature_selection import mutual_info_classif
        corr = X.corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]
        X_reduced = X.drop(columns=to_drop)
        
        mi = mutual_info_classif(X_reduced.fillna(0), y)
        mi_series = pd.Series(mi, index=X_reduced.columns).sort_values(ascending=False)
        selected_cols = mi_series.index[:min(N_KEEP, len(mi_series))].tolist()
    
    X_sel = X[selected_cols].copy()
    print(f"      Selected {len(selected_cols)} features")
    
    # 5. Feature engineering
    print("[5/7] Adding engineered features...")
    mean_vec = X_sel.mean(axis=0).values
    euclid = np.linalg.norm(X_sel.values - mean_vec, axis=1)
    X_sel['euclidean_distance'] = euclid
    
    # 6. Train model
    print("[6/7] Training model...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_sel)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train Decision Tree (best performer from paper)
    model = DecisionTreeClassifier(random_state=42, max_depth=10)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("\n" + "="*60)
    print("MODEL EVALUATION")
    print("="*60)
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
    
    # Calculate detailed metrics
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    # Prepare results for CSV
    results_data = {
        'timestamp': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
        'model': ['DecisionTree'],
        'accuracy': [accuracy],
        'precision': [precision],
        'recall': [recall],
        'f1_score': [f1],
        'num_features': [len(selected_cols) + 1],  # +1 for euclidean distance
        'train_samples': [len(X_train)],
        'test_samples': [len(X_test)]
    }
    
    results_df = pd.DataFrame(results_data)
    
    # Save or append to CSV
    results_csv_path = './models/model_results.csv'
    try:
        # Try to append to existing file
        existing_results = pd.read_csv(results_csv_path)
        results_df = pd.concat([existing_results, results_df], ignore_index=True)
    except FileNotFoundError:
        # File doesn't exist, will create new one
        pass
    
    results_df.to_csv(results_csv_path, index=False)
    print(f"[✓] Results saved to: {results_csv_path}")
    
    # 7. Export model
    print("[7/7] Exporting model...")
    model_data = {
        'model': model,
        'scaler': scaler,
        'features': selected_cols + ['euclidean_distance'],
        'training_date': pd.Timestamp.now().isoformat(),
        'performance': {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    }
    
    output_path = './models/mqtt_ids_model.joblib'
    joblib.dump(model_data, output_path)
    print(f"[✓] Model saved to: {output_path}")
    print("\nYou can now use this model with live_ids.py!")

if __name__ == "__main__":
    train_and_export_model()
