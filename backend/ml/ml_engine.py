import os
import joblib
import numpy as np
import pandas as pd
from collections import deque
import time

class MLEngine:
    def __init__(self, model_path="fatigue_model.pkl"):
        self.model = None
        self.model_path = model_path
        self.labels = {0: "Alert", 1: "Drowsy", 2: "Fatigued"}
        
        # INDUSTRIAL UPGRADE: Feature Window
        self.window_size = 20  # WIDE window for "Movie-like" smoothing
        self.history = deque(maxlen=self.window_size)
        
        # ADVANCED SMOOTHING: Exponential Moving Average (EMA)
        self.ema_probs = None 
        self.alpha = 0.15 # VERY LOW = Slow, cinematic transitions
        
        # SAFETY CRITICAL: Microsleep Detection
        # Thresholds now rely on external frame counting for accuracy
        self.microsleep_max_frames = 10   # ~0.33s
        
        # STATE MACHINE: Hysteresis (Sticky States)
        self.current_state = 0 # Default Alert
        self.state_persistence = 0
        self.required_persistence = 5 # Frames to hold before switching
        
        self.debug_counter = 0

        # ROBUSTNESS 2.0: Adaptive Calibration
        self.base_ear = 0.32   # Dynamic baseline
        self.calibration_frames = 0
        self.max_calibration = 100 # Frames to learn 'Normal' EAR
        
        # Sensor Integrity
        self.last_sensor_values = {"hr": 0, "temp": 0}
        self.sensor_stale_count = 0
        
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
        
        if len(self.history) < 2:
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
            return {"status": "Unknown", "confidence": 0, "raw_probs": [0,0,0]}

        # --- 0. VALIDITY CHECK (SAFETY FIRST) ---
        status = vision_data.get("status", "Unknown")
        if status in ["No Face", "Unstable"]:
            # If no face is visible, we should not feed the model garbage data (EAR=0).
            # We decay the probability back towards Alert (0) to prevent stuck alarms.
            if self.ema_probs is not None:
                # Slowly drift towards Alert (0.1% chance shift per frame)
                target_probs = np.array([1.0, 0.0, 0.0])
                self.ema_probs = (0.05 * target_probs) + (0.95 * self.ema_probs)
                
                # Update current state based on drifted probs
                self.current_state = np.argmax(self.ema_probs)
            
            return {
                "status": self.labels.get(self.current_state, "Unknown"),
                "confidence": round(float(np.max(self.ema_probs)), 2) if self.ema_probs is not None else 0,
                "raw_probs": [round(p, 2) for p in self.ema_probs] if self.ema_probs is not None else [1,0,0],
                "flag": f"SKIPPED_{status.upper().replace(' ', '_')}"
            }

        try:
             # --- 1. ROBUST SENSOR IMPUTATION ---
            # Sensors (Arduino) might fail or return 0. We must NOT feed 0 into the model.
            
            # Default "Population Average" values (Fallback of last resort)
            DEFAULT_HR = 75.0
            DEFAULT_TEMP = 37.0
            
            # Check current readings
            curr_hr = sensor_data.get('hr', 0)
            curr_temp = sensor_data.get('temperature', 0)
            
            # If invalid (<=0), try to use history mean, else use default
            if curr_hr <= 0:
                if len(self.history) > 0:
                     # Calculate simple mean of valid HRs in history
                     valid_hrs = [frame[4] for frame in self.history if frame[4] > 0]
                     curr_hr = np.mean(valid_hrs) if valid_hrs else DEFAULT_HR
                else:
                    curr_hr = DEFAULT_HR
                    
            if curr_temp <= 0:
                if len(self.history) > 0:
                     valid_temps = [frame[5] for frame in self.history if frame[5] > 0]
                     curr_temp = np.mean(valid_temps) if valid_temps else DEFAULT_TEMP
                else:
                    curr_temp = DEFAULT_TEMP

            current_ear_raw = vision_data.get('ear', 0.3)
            current_mar = vision_data.get('mar', 0.0)
            closed_frames = vision_data.get('closed_frames', 0)
            
            head_yaw = abs(vision_data.get('head_angle_y', 0))
            head_pitch = abs(vision_data.get('head_angle_x', 0))

            # --- 2. POSE-BASED EAR CORRECTION ---
            # If head is turned (Yaw), EAR naturally decreases visually.
            # Correction: Slightly boost EAR if looking away to prevent false fatigue.
            correction_factor = 1.0 + (head_yaw / 90.0) * 0.2
            current_ear = current_ear_raw * correction_factor

            # --- 3. SENSOR INTEGRITY GUARD ---
            # Detect if Arduino is sending 'Frozen' data (Stuck sensor)
            if curr_hr == self.last_sensor_values["hr"] and curr_hr > 0:
                self.sensor_stale_count += 1
            else:
                self.sensor_stale_count = 0
                self.last_sensor_values["hr"] = curr_hr
            
            sensor_reliable = self.sensor_stale_count < 50 # Unreliable if stuck for 50 frames
            
            # --- 4. ADAPTIVE BASELINE CALIBRATION ---
            # Learn what 'Alert' looks like for THIS specific user
            if self.current_state == 0 and not closed_frames:
                if self.calibration_frames < self.max_calibration:
                    self.calibration_frames += 1
                    # Running Average for Baseline
                    self.base_ear = (self.base_ear * 0.95) + (current_ear * 0.05)

            # DEBUG LOGGING (Throttle to ~every 5 seconds)
            self.debug_counter += 1
            if self.debug_counter % 20 == 0:
                 print(f"[ML ROBUST] EAR: {current_ear:.3f} (Base: {self.base_ear:.2f}) | Yaw: {head_yaw:.1f} | Reliable: {sensor_reliable}")

            # MICROSLEEP DETECTION (Use reliable frame counter)
            # If eyes closed for > 15 frames (~0.5s), FORCE FATIGUE
            if closed_frames > self.microsleep_max_frames:
                print(f"[ML SAFETY] Microsleep Detected! ({closed_frames} frames)")
                self.current_state = 2 # Force state
                return {
                    "status": "Fatigued",
                    "confidence": 1.0,
                    "raw_probs": [0.0, 0.0, 1.0], # Force probability
                    "flag": "MICROSLEEP"
                }

            # FALLBACK: High PERCLOS (Eyes closing frequently)
            # If PERCLOS > 55%, user is definitely tired regardless of other features.
            current_perclos = vision_data.get('perclos', 0.0)
            if current_perclos > 55.0:
                print(f"[ML SAFETY] High PERCLOS ({current_perclos}%) Detected!")
                self.current_state = 2
                return {
                    "status": "Fatigued",
                    "confidence": 1.0,
                    "raw_probs": [0.0, 0.0, 1.0],
                    "flag": "HIGH_PERCLOS"
                }

            # --- 2. FEATURE ENGINEERING ---
            raw_sample = [
                current_ear,
                current_mar,
                vision_data.get('head_angle_x', 0), # Pitch
                vision_data.get('head_angle_y', 0), # Yaw
                curr_hr,    # IMPUTED
                curr_temp   # IMPUTED
            ]
            
            stats = self.calculate_temporal_features(raw_sample)
            
            feature_vector = [
                vision_data.get('perclos', 0),
                stats['ear_mean'], stats['ear_std'],
                stats['mar_mean'], stats['mar_std'],
                stats['pitch_mean'], stats['pitch_std'],
                stats['hr_mean'], stats['hr_std'],
                stats['temp_mean']
            ]
            
            feature_names = [
                'perclos', 
                'ear_mean', 'ear_std', 
                'mar_mean', 'mar_std', 
                'head_pitch_mean', 'head_pitch_std', 
                'hr_mean', 'hr_std',
                'temperature_mean'
            ]
            X_input = pd.DataFrame([feature_vector], columns=feature_names)
            
            # --- 3. PROBABILISTIC INFERENCE ---
            # Get raw probabilities [Alert%, Drowsy%, Fatigued%]
            raw_probs = self.model.predict_proba(X_input)[0]
            
            # --- 4. ADVANCED SMOOTHING (EMA) ---
            if self.ema_probs is None:
                self.ema_probs = raw_probs
            else:
                # Update EMA: New = alpha * current + (1 - alpha) * old
                self.ema_probs = (self.alpha * raw_probs) + ((1 - self.alpha) * self.ema_probs)
                
            # Normalize to sum to 1
            self.ema_probs /= np.sum(self.ema_probs)
            
            # --- 5. HYSTERESIS / STATE MACHINE ---
            # 0: Alert, 1: Drowsy, 2: Fatigued
            
            proposed_state = np.argmax(self.ema_probs)
            confidence = self.ema_probs[proposed_state]
            
            # Transition Logic
            # "Movie-like" Progression: Alert (0) <-> Drowsy (1) <-> Fatigued (2)
            # You generally shouldn't jump from Alert to Fatigued instantly unless it's a safety override (handled above).
            
            # 1. Enforce Sequential Steps if possible
            if self.current_state == 0 and proposed_state == 2:
                 # IF attempting to jump Alert -> Fatigued, force Drowsy first unless confidence is MASSIVE
                 if confidence < 0.9:
                     proposed_state = 1
                     
            if self.current_state == 2 and proposed_state == 0:
                 # IF attempting to jump Fatigued -> Alert, force Drowsy first
                 proposed_state = 1

            # 2. Persistence Check (Must hold state for N frames)
            if proposed_state != self.current_state:
                self.state_persistence += 1
                if self.state_persistence >= self.required_persistence:
                     self.current_state = proposed_state
                     self.state_persistence = 0
            else:
                self.state_persistence = 0
            
            final_label = self.labels.get(self.current_state, "Unknown")
            
            return {
                "status": final_label,
                "confidence": round(float(confidence), 2),
                "raw_probs": [round(p, 2) for p in self.ema_probs]
            }
            
        except Exception as e:
            print(f"[ML ERROR] {e}")
            return {"status": "Error", "confidence": 0}
