
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
print("Generating temporal features (Rolling statistics)...")

df = df.sort_values(by=['session_id', 'timestamp'])

base_features = ['ear', 'mar', 'head_pitch', 'head_yaw', 'hr', 'temperature']

for col in base_features:
    df[f'{col}_mean'] = df.groupby('session_id')[col].transform(lambda x: x.rolling(window=WINDOW_SIZE, min_periods=1).mean())
    df[f'{col}_std'] = df.groupby('session_id')[col].transform(lambda x: x.rolling(window=WINDOW_SIZE, min_periods=1).std())

df = df.fillna(0)

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

print("Training Temporal Random Forest...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)
model.fit(X_train, y_train)

preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
print(f"✅ Accuracy with Temporal Features: {acc:.4f}")
print("\nClassification Report:\n", classification_report(y_test, preds))

joblib.dump(model, MODEL_FILE)
print(f"✅ Enhanced Industry-Model saved to {MODEL_FILE}")
