import os
import joblib
import numpy as np
import pandas as pd
from collections import deque

class MLEngine:
    def __init__(self, model_path="fatigue_model.pkl"):
        self.model = None
        self.model_path = model_path
        self.labels = {0: "Alert", 1: "Drowsy", 2: "Fatigued"}
        
        # INDUSTRIAL UPGRADE: Feature Window & Prediction Buffer
        self.window_size = 5 # For temporal features
        self.history = deque(maxlen=self.window_size)
        
        # OUTPUT SMOOTHING: Keep last N predictions to vote
        self.prediction_buffer = deque(maxlen=10) # ~0.5 - 1 second buffer
        
        self.load_model()

    def load_model(self):
        """Loads the trained ML model from disk."""
        if not os.path.exists(self.model_path):
            print(f"[ML] ⚠️ Model file not found at {self.model_path}.")
            return

        try:
            self.model = joblib.load(self.model_path)
            print(f"[ML] ✅ Model loaded successfully from {self.model_path}")
        except Exception as e:
            print(f"[ML] ❌ Failed to load model: {e}")

    def calculate_temporal_features(self, current_data):
        """Computes rolling mean/std from history."""
        self.history.append(current_data)
        data_matrix = np.array(self.history)
        
        # Handle edge case where we don't have enough history yet
        if len(self.history) < 2:
            # Return current values as mean, 0 as std
            return {
                'ear_mean': current_data[0], 'ear_std': 0,
                'mar_mean': current_data[1], 'mar_std': 0,
                'pitch_mean': current_data[2], 'pitch_std': 0,
                'hr_mean': current_data[4], 'hr_std': 0,
                'temp_mean': current_data[5]
            }

        means = np.mean(data_matrix, axis=0)
        stds = np.std(data_matrix, axis=0)
        
        return {
            'ear_mean': means[0], 'ear_std': stds[0],
            'mar_mean': means[1], 'mar_std': stds[1],
            'pitch_mean': means[2], 'pitch_std': stds[2],
            'hr_mean': means[4], 'hr_std': stds[4],
            'temp_mean': means[5]
        }

    def predict(self, sensor_data, vision_data):
        if self.model is None:
            return {"status": "Unknown", "confidence": 0}

        try:
            # 1. STANDARDIZE INPUT
            raw_sample = [
                vision_data.get('ear', 0),
                vision_data.get('mar', 0),
                vision_data.get('head_angle_x', 0),
                vision_data.get('head_angle_y', 0),
                sensor_data.get('hr', 70),
                sensor_data.get('temperature', 37)
            ]
            
            # 2. TEMPORAL FEATURES
            stats = self.calculate_temporal_features(raw_sample)
            
            # 3. FEATURE VECTOR
            feature_vector = [
                vision_data.get('perclos', 0),
                stats['ear_mean'], stats['ear_std'],
                stats['mar_mean'], stats['mar_std'],
                stats['pitch_mean'], stats['pitch_std'],
                stats['hr_mean'], stats['hr_std'],
                stats['temp_mean']
            ]
            

            # 4. PREDICT PROBABILITY
            # Use DataFrame with feature names to silence sklearn warning
            feature_names = [
                'perclos', 
                'ear_mean', 'ear_std', 
                'mar_mean', 'mar_std', 
                'head_pitch_mean', 'head_pitch_std', 
                'hr_mean', 'hr_std',
                'temperature_mean'
            ]
            X_input = pd.DataFrame([feature_vector], columns=feature_names)
            
            # Get probabilities [Alert%, Drowsy%, Fatigued%]
            probs = self.model.predict_proba(X_input)[0]
            raw_pred_idx = np.argmax(probs)
            
            # 5. SMOOTHING (Debouncing)
            # Add raw prediction to buffer
            self.prediction_buffer.append(raw_pred_idx)
            
            # Majority Vote: What is the most frequent class in buffer?
            final_pred_idx = max(set(self.prediction_buffer), key=self.prediction_buffer.count)
            
            final_label = self.labels.get(final_pred_idx, "Unknown")
            final_conf = round(float(probs[final_pred_idx]), 2) # Confidence of the FINAL vote based on current frame prop
            
            return {
                "status": final_label,
                "confidence": final_conf,
                "raw_probs": [round(p, 2) for p in probs]
            }
            
        except Exception as e:
            print(f"[ML ERROR] {e}")
            return {"status": "Error", "confidence": 0}
