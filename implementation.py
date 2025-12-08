"""
Exact implementation pipeline from the paper:
"Enhancing MQTT Intrusion Detection in IoT Using Machine Learning and Feature Engineering"

This script implements the paper's preprocessing, feature selection, feature engineering,
and evaluation pipeline. It attempts to reproduce the authors' exact steps and also
contains an explicit place where you can paste the exact 21-feature list (Table 6)
if you extract it from the PDF. If that exact list is not provided, the script will
use the hybrid PCC (0.95) + mutual information strategy from the paper to select
21 features automatically.

How to use
----------
1. Place the RT-IoT2022 CSV in the same folder and set DATA_PATH.
2. If you have the exact 21 features from Table 6, paste them into FEATURES_LIST.
   If FEATURES_LIST is left None, the script will perform PCC + MI to pick 21 features.
3. Run the script in a Python environment with the usual libs installed:
   pandas, numpy, scikit-learn, scipy, pdfplumber (optional), matplotlib (optional).

Outputs
-------
- Prints dataset loading info, selected features, and model metrics (mean + 95% CI over 10 seeds)
- Saves a CSV of the selected features (selected_features.csv) and a pickle of the trained models if desired.

NOTE: Exact reproduction of the paper's numbers requires using the exact column list
from Table 6. Use the FEATURES_LIST variable below to force exact selection.
"""

import math
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import mutual_info_classif
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score)

from configs import *
from utils import *

# 1. Load data
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
print("Dataset shape:", df.shape)

# 2. Label column
label_col = find_label_column(df)
print("Detected label column:", label_col)

y_raw = df[label_col]

y = binary_encode_labels(y_raw)
print("Binary target distribution (0 benign / 1 attack):")
print(pd.Series(y).value_counts())

# 3. Drop 'service' and 'proto' if present (paper removed them)
for col in ['service','proto']:
    if col in df.columns:
        print(f"Dropping column as in paper: {col}")
        df = df.drop(columns=[col])

# 4. Separate features
X = df.drop(columns=[label_col]).copy()

# 5. Convert/clean non-numeric columns
for c in X.select_dtypes(include=['object']).columns:
    try:
        X[c] = pd.to_numeric(X[c])
    except Exception:
        print(f"Dropping non-numeric column: {c}")
        X = X.drop(columns=[c])

print("Feature shape after dropping non-numeric:", X.shape)

# 6. Drop constant cols
nunique = X.nunique()
const_cols = nunique[nunique <= 1].index.tolist()
if const_cols:
    print("Dropping constant columns:", const_cols)
    X = X.drop(columns=const_cols)

# 7. If user supplied exact FEATURES_LIST, use it. Otherwise run PCC(0.95) + MI to pick top N_KEEP.
if FEATURES_LIST is not None:
    # Validate
    missing = [c for c in FEATURES_LIST if c not in X.columns]
    if missing:
        raise RuntimeError(f"The FEATURES_LIST contains columns not in the dataset: {missing}")
    selected_cols = FEATURES_LIST
    print("Using user-supplied exact features list with {} features.".format(len(selected_cols)))
else:
    print("No exact features provided. Running PCC pruning (0.95) then MI ranking to pick top {} features...".format(N_KEEP))
    # PCC pruning
    corr = X.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]
    print(f"Dropping {len(to_drop)} highly correlated features (PCC > 0.95)")
    X_reduced = X.drop(columns=to_drop)
    # Mutual information ranking
    mi = mutual_info_classif(X_reduced.fillna(0), y)
    mi_series = pd.Series(mi, index=X_reduced.columns).sort_values(ascending=False)
    selected_cols = mi_series.index[:min(N_KEEP, len(mi_series))].tolist()
    print(f"Selected {len(selected_cols)} features by MI after PCC-reduction")

# 8. Keep selected columns and save a CSV of selected features
X_sel = X[selected_cols].copy()
# X_sel.to_csv('./data/selected_features.csv', index=False)
# print("Saved selected features to selected_features.csv")

# 9. Feature engineering: Euclidean distance-to-mean feature
mean_vec = X_sel.mean(axis=0).values
euclid = np.linalg.norm(X_sel.values - mean_vec, axis=1)
X_sel['euclidean_distance'] = euclid
print("Added 'euclidean_distance' feature. New shape:", X_sel.shape)

# 10. Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sel)

# 11. Define models
models = {
    'DecisionTree': DecisionTreeClassifier(random_state=0),
    'kNN': KNeighborsClassifier(n_neighbors=KNN_K)
}

# 12. Train and evaluate across seeds
results = {m: {'accuracy':[], 'precision':[], 'recall':[], 'f1':[], 'specificity':[], 'fpr':[], 'auc':[]} for m in models}

for seed in SEEDS:
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=TEST_SIZE, random_state=seed, stratify=None)
    for name, clf in models.items():
        # set random state if exists
        if 'random_state' in clf.get_params():
            clf.set_params(random_state=seed)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        try:
            probs = clf.predict_proba(X_test)[:,1]
            roc = roc_auc_score(y_test, probs)
        except Exception:
            roc = float('nan')
        results[name]['accuracy'].append(accuracy_score(y_test, y_pred))
        results[name]['precision'].append(precision_score(y_test, y_pred, zero_division=0))
        results[name]['recall'].append(recall_score(y_test, y_pred, zero_division=0))
        results[name]['f1'].append(f1_score(y_test, y_pred, zero_division=0))
        results[name]['specificity'].append(specificity_score(y_test, y_pred))
        results[name]['fpr'].append(false_positive_rate(y_test, y_pred))
        results[name]['auc'].append(roc)

# 13. Print mean + 95% CI
print("\n=== Results (mean and 95% CI across seeds) ===")
for name in models:
    print(f"\nModel: {name}")
    for metric in ['accuracy','precision','recall','f1','specificity','fpr','auc']:
        vals = results[name][metric]
        vals_clean = [v for v in vals if not (isinstance(v, float) and math.isnan(v))]
        if len(vals_clean) == 0:
            print(f" {metric}: no values")
            continue
        m, (lo, hi) = ci_95(vals_clean)
        print(f" {metric:10s}: {m:.4f}  (95% CI: {lo:.4f} - {hi:.4f})")

print("\nDone.")
