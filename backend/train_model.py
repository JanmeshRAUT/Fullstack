
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# 1. SETUP
DATA_FILE = "fatigue_dataset.csv"
MODEL_FILE = "fatigue_model.pkl"
WINDOW_SIZE = 5  # 5 samples * 2s interval = 10 seconds history

print(f"Loading data from {DATA_FILE}...")
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    print(f"❌ {DATA_FILE} not found!")
    exit()

# 2. TEMPORAL FEATURE ENGINEERING (The Industry Upgrade)
# We must group by Session to ensure we don't roll features across different users/drives
print("Generating temporal features (Rolling statistics)...")

df = df.sort_values(by=['session_id', 'timestamp'])

# Define base features to aggregate
base_features = ['ear', 'mar', 'head_pitch', 'head_yaw', 'hr', 'temperature']

# Calculate Rolling Mean (Trend) and Rolling Std (Variability)
for col in base_features:
    # Mean: Smooths out noise, shows trend (e.g., Body temp rising, Eyes getting closer)
    df[f'{col}_mean'] = df.groupby('session_id')[col].transform(lambda x: x.rolling(window=WINDOW_SIZE, min_periods=1).mean())
    # Std: Shows volatility (e.g., Head nodding = high pitch variance, HRV = high hr variance)
    df[f'{col}_std'] = df.groupby('session_id')[col].transform(lambda x: x.rolling(window=WINDOW_SIZE, min_periods=1).std())

# Fill NaNs created by rolling (first few rows) with 0 or the row's own value
df = df.fillna(0)

# 3. FINAL FEATURE SELECTION
# We use the NEW rich features + key instantaneous ones like PERCLOS
features = [
    'perclos', 
    'ear_mean', 'ear_std', 
    'mar_mean', 'mar_std', 
    'head_pitch_mean', 'head_pitch_std', 
    'hr_mean', 'hr_std',
    'temperature_mean'
]
target = 'fatigue_label'

print(f"Feature Vector ({len(features)}): {features}")

X = df[features]
y = df[target]

# 4. TRAIN (Robust Random Forest)
print("Training Temporal Random Forest...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Increased estimators for stability
model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)
model.fit(X_train, y_train)

# 5. EVALUATE
preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
print(f"✅ Accuracy with Temporal Features: {acc:.4f}")
print("\nClassification Report:\n", classification_report(y_test, preds))

# 6. SAVE
joblib.dump(model, MODEL_FILE)
print(f"✅ Enhanced Industry-Model saved to {MODEL_FILE}")
