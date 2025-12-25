import pandas as pd
import numpy as np
import pickle
import os
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split

# Config
DATASET_PATH = r"fatigue_dataset.csv"
MODEL_SAVE_PATH = "fatigue_lstm.h5"
SCALER_SAVE_PATH = "scaler.pkl"
ENCODER_SAVE_PATH = "encoder.pkl"
LOOKBACK = 10  # Number of time steps to look back

def create_sequences(data, target, lookback):
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i:i+lookback])
        y.append(target[i+lookback])
    return np.array(X), np.array(y)

def train_lstm():
    print("Loading dataset for LSTM...")
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    try:
        # Load and Clean
        df = pd.read_csv(DATASET_PATH)
        df.dropna(how='all', inplace=True)
        
        print("Columns:", df.columns.tolist())
        
        # MAPPING NEW DATASET COLUMNS TO MODEL FEATURES
        # Actual Columns: ['timestamp', 'subject_id', 'session_id', 'temperature', 'hr', 'spo2', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'perclos', 'ear', 'mar', 'yawn_status', 'head_pitch', 'head_yaw', 'fatigue_label']
        
        # 1. Map Features
        # The columns already match the model expectation perfectly!
        # Features needed: ['temperature', 'hr', 'spo2', 'perclos', 'ear', 'mar']
        
        # Just ensure they are numeric
        pass # No renaming needed except ensuring `mar` is correct.
        
        # 'mar' exists in dataset, so use it directly.
        
        # Update Features List
        features = ['temperature', 'hr', 'spo2', 'perclos', 'ear', 'mar']
        
        # TARGET
        target_col = 'fatigue_label'
        
        if target_col not in df.columns:
             print(f"Error: Target column '{target_col}' not found. Available: {df.columns.tolist()}")
             return
        
        # Ensure numeric
        for col in features:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.dropna(subset=features + [target_col], inplace=True)
        
        # Encode Target (String -> Int)
        # e.g., 'Alert', 'Drowsy' -> 0, 1
        encoder = LabelEncoder()
        df['target_encoded'] = encoder.fit_transform(df[target_col])
        
        # Use encoded target for sequence creation
        target_series = df['target_encoded']
        
        # One-hot encode for training
        num_classes = len(encoder.classes_)
        categorical_labels = to_categorical(target_series, num_classes=num_classes)
        
        # Feature Scaling
        print("Scaling features...")
        scaler = MinMaxScaler()
        scaled_features = scaler.fit_transform(df[features])
        
        # Create Sequences
        print(f"Creating sequences with lookback {LOOKBACK}...")
        X, y = create_sequences(scaled_features, categorical_labels, LOOKBACK)
        
        if len(df) < LOOKBACK + 10:
            print("Not enough data for LSTM training.")
            return


        # Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
        
        print(f"Training shape: {X_train.shape}")

        # Build LSTM Model
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(LOOKBACK, len(features))),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(y.shape[1], activation='softmax')
        ])
        
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        
        # Train
        model.fit(X_train, y_train, epochs=20, batch_size=32, validation_data=(X_test, y_test), verbose=1)
        
        # Evaluate
        loss, acc = model.evaluate(X_test, y_test)
        print(f"Test Accuracy: {acc*100:.2f}%")
        
        # Save Artifacts
        model.save(MODEL_SAVE_PATH)
        with open(SCALER_SAVE_PATH, 'wb') as f:
            pickle.dump(scaler, f)
        with open(ENCODER_SAVE_PATH, 'wb') as f:
            pickle.dump(encoder, f)
            
        print(f"✅ LSTM Model saved to {MODEL_SAVE_PATH}")
        print(f"✅ Scaler & Encoder saved.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    train_lstm()
