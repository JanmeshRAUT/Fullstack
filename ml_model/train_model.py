import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import os

# Paths
DATASET_PATH = r"..\backend\auto_labeled_fatigue_dataset.csv"
MODEL_SAVE_PATH = "fatigue_model.pkl"

def train_model():
    print("Loading dataset...")
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    try:
        # Load dataset
        df = pd.read_csv(DATASET_PATH)
        
        # Basic cleanup - handle potential header mismatches or empty lines
        df.dropna(how='all', inplace=True) 
        
        print(f"Dataset shape: {df.shape}")
        print("Columns:", df.columns.tolist())

        # Feature Selection
        # We want to use sensor data + computer vision features
        # Assuming columns based on inspection: temperature, hr, spo2, perclos, ear, mar
        # 'yawn_status' is categorical, we can encode it or skip it if 'mar' covers it. 
        # Let's use 'mar' as it is continuous.
        
        features = ['temperature', 'hr', 'spo2', 'perclos', 'ear', 'mar']
        target = 'auto_label'

        # Check if features exist
        missing_cols = [c for c in features if c not in df.columns]
        if missing_cols:
            print(f"Warning: Missing columns {missing_cols}. Trying to match closely...")
            # Fallback logic could go here, but for now let's strict check
            return

        X = df[features]
        y = df[target]

        # Cleanup numeric columns (force numeric, coerce errors to NaN)
        for col in features:
            X.loc[:, col] = pd.to_numeric(X[col], errors='coerce')

        # Drop rows with NaNs in features
        # Combine back temporarily to drop
        data_clean = pd.concat([X, y], axis=1).dropna()
        X = data_clean[features]
        y = data_clean[target]

        if len(X) < 10:
            print("Not enough clean data to train. Need at least 10 rows.")
            return

        print(f"Training on {len(X)} samples...")

        # Train/Test Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Initialize Model
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Train
        clf.fit(X_train, y_train)

        # Evaluate
        y_pred = clf.predict(X_test)
        print("Accuracy:", accuracy_score(y_test, y_pred))
        print("\nClassification Report:\n", classification_report(y_test, y_pred))

        # Save Model
        with open(MODEL_SAVE_PATH, 'wb') as f:
            pickle.dump(clf, f)
        
        print(f"Model saved to {MODEL_SAVE_PATH}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    train_model()
