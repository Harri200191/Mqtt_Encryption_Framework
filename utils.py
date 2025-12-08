from configs import *
from sklearn.metrics import confusion_matrix
import numpy as np
import pandas as pd
import math
from scipy import stats

def find_label_column(df):
    if LABEL_COL_OVERRIDE and LABEL_COL_OVERRIDE in df.columns:
        return LABEL_COL_OVERRIDE
    candidates = ['label','Label','target','class','Category','attack_type']
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        if df[c].dtype == object and df[c].nunique() < 50:
            return c
    raise RuntimeError("Could not find label column automatically. Set LABEL_COL_OVERRIDE if needed.")

def specificity_score(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return tn / (tn + fp) if (tn + fp) > 0 else 0.0

def false_positive_rate(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return fp / (fp + tn) if (fp + tn) > 0 else 0.0

def ci_95(x):
    a = np.array(x)
    m = a.mean()
    se = a.std(ddof=1) / math.sqrt(len(a))
    h = se * stats.t.ppf(0.975, len(a)-1)
    return m, (m - h, m + h)

def binary_encode_labels(y_series):
    y = y_series.astype(str).str.strip().str.lower()
    return (y != "mqtt_publish".lower()).astype(int)
