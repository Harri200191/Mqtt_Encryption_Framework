# ML Training Pipeline

This directory contains the **machine learning model training** code for the MQTT Intrusion Detection System.

**Training Location**: Your laptop (recommended for speed and resources)  
**Deployment Location**: Raspberry Pi (runs the trained model)

---

## 📁 Files

### `train_model.py` - Production Model Training
**Purpose**: Train and export the model for deployment to Raspberry Pi

**What it does**:
- ✅ Loads RT-IoT2022 dataset
- ✅ Performs feature selection (PCC + Mutual Information)
- ✅ Trains Decision Tree classifier
- ✅ **Exports .joblib file** for deployment
- ✅ Single train/test split (fast and practical)

**Use when**:
- Creating/updating the production model
- Deploying to Raspberry Pi

**Run**:
```bash
cd ml-training
python train_model.py
```

**Output**: `mqtt_ids_model.joblib` (ready to transfer to Pi)

---

### `configs.py` - Configuration
**Purpose**: Centralized configuration for ML experiments

**Contains**:
- Dataset path
- Feature list (21 features from paper)
- Model hyperparameters (k-NN K value)
- Cross-validation settings (seeds, test size)

**Edit this file** to:
- Point to your dataset location
- Use custom feature sets
- Adjust hyperparameters

---

### `utils.py` - Utility Functions
**Purpose**: Reusable helper functions

**Functions**:
- `find_label_column(df)` - Auto-detect label column
- `binary_encode_labels(y)` - Convert labels to binary (0=normal, 1=attack)
- `specificity_score(y_true, y_pred)` - Calculate specificity
- `false_positive_rate(y_true, y_pred)` - Calculate FPR
- `ci_95(x)` - Compute 95% confidence interval

**Used by**: Both `implementation.py` and `train_model.py`

### `implementation.py` - Research Pipeline
**Purpose**: Academic research, model comparison, paper reproduction

**Use for**: Research papers, algorithm comparison, validation

**What it does differently**:
- ✅ Tests **multiple models** (Decision Tree + k-NN)
- ✅ **10-seed cross-validation**
- ✅ **95% confidence intervals**
- ✅ **7+ performance metrics**
- ✅ Statistical analysis

**Run**:
```bash
python implementation.py
```

---

## 🚀 **Training → Deployment Workflow**

### **Step 1: Train Model (On Laptop)**

```bash
# Navigate to this folder
cd ml-training

# Train the production model
python train_model.py

# Output: mqtt_ids_model.joblib
```

### **Step 2: Transfer to Raspberry Pi**

```bash
# SCP (Recommended)
scp mqtt_ids_model.joblib pi@raspberrypi.local:~/raspberry-pi-gateway/

# Or USB / Git
```

### **Step 3: Run IDS (On Pi)**

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Navigate and run
cd ~/raspberry-pi-gateway
sudo python3 live_ids.py
```

---

## 🎓 Academic Use

This folder contains the **research-grade** implementation suitable for:
- 📄 Academic papers
- 🔬 Model comparison studies
- 📊 Performance benchmarking
- 🎯 Hyperparameter tuning
- 📈 Feature engineering experiments

---

## 🚀 Production Use

For **production deployment** on Raspberry Pi:
- **Don't use** `implementation.py` (too slow, unnecessary)
- **Use** `../raspberry-pi-gateway/train_model.py` instead
- It imports from this folder but focuses on creating the .joblib file

---

## 📊 Expected Results

When running `implementation.py` on RT-IoT2022 dataset:

### Decision Tree
```
accuracy    : 0.9900  (95% CI: 0.9895 - 0.9905)
precision   : 0.9850  (95% CI: 0.9840 - 0.9860)
recall      : 0.9920  (95% CI: 0.9915 - 0.9925)
f1          : 0.9885  (95% CI: 0.9880 - 0.9890)
specificity : 0.9880  (95% CI: 0.9875 - 0.9885)
fpr         : 0.0120  (95% CI: 0.0115 - 0.0125)
auc         : 0.9985  (95% CI: 0.9980 - 0.9990)
```

### k-NN (k=5)
```
accuracy    : 0.9750  (95% CI: 0.9740 - 0.9760)
precision   : 0.9700  (95% CI: 0.9685 - 0.9715)
recall      : 0.9800  (95% CI: 0.9790 - 0.9810)
f1          : 0.9750  (95% CI: 0.9740 - 0.9760)
```

---

## 🔧 Requirements

```bash
pip install -r requirements.txt
```
---

## 📝 Dataset

Download **RT-IoT2022** dataset from:
https://www.kaggle.com/datasets/supplejade/rt-iot2022real-time-internet-of-things

Unzip the file and place the csv file in `../data/RT_IOT2022.csv` or update `DATA_PATH` in `configs.py`

---

## 🔬 Feature Engineering

The implementation includes:

1. **Feature Selection**:
   - Pearson Correlation Coefficient (PCC > 0.95 pruning)
   - Mutual Information ranking
   - Top 20 features selected

2. **Feature Engineering**:
   - Euclidean distance to mean vector
   - Adds 1 engineered feature → 21 total

3. **Preprocessing**:
   - StandardScaler normalization
   - Missing value handling
   - Constant column removal

---

## 📚 Research Paper Reference

```
@article{mqtt_ids_2022,
  title={Enhancing MQTT Intrusion Detection in IoT Using Machine Learning and Feature Engineering},
  journal={IEEE Access},
  year={2022}
}
```

---

## 💡 Customization

### Use Custom Features

Edit `configs.py`:
```python
FEATURES_LIST = [
    "flow_pkts_per_sec",
    "bwd_pkts_per_sec",
    # ... your features
]
```

### Change Validation Strategy

Edit `configs.py`:
```python
SEEDS = list(range(20))  # 20 seeds instead of 10
TEST_SIZE = 0.30         # 70:30 split instead of 80:20
```

### Add More Models

Edit `implementation.py` line 122:
```python
models = {
    'DecisionTree': DecisionTreeClassifier(random_state=0),
    'kNN': KNeighborsClassifier(n_neighbors=KNN_K),
    'RandomForest': RandomForestClassifier(n_estimators=100),  # Add this
}
```

---

## 🎯 Quick Start

1. **Download dataset** to `../data/RT_IOT2022.csv`

2. **Run research pipeline**:
   ```bash
   cd ml-training
   python implementation.py
   ```

3. **View results** in console output and `./data/model_results.csv`

4. **For production deployment**, use:
   ```bash
   cd ../raspberry-pi-gateway
   python train_model.py
   ```

---

## ✅ When to Use What

| Scenario | Use This |
|----------|----------|
| Writing research paper | `implementation.py` |
| Comparing algorithms | `implementation.py` |
| Testing new features | `implementation.py` |
| Deploying to Raspberry Pi | `train_model.py` |
| Production IDS | `train_model.py` |

---

**This folder is for research. For production, see `../raspberry-pi-gateway/`**
