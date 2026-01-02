from flask import Blueprint, jsonify, request
import time
import base64
import cv2
import numpy as np
import threading
import os
import traceback

from cv.perclos import process_face_mesh, perclos_data
from cv.head_pose import cv_head_angles, cv_angles_lock
from sensors.serial_reader import latest_sensor_data, sensor_data_history, head_position_data, calculate_head_position
from ml.ml_engine import MLEngine

api_bp = Blueprint('api', __name__)

# --- ML Engine & State ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "fatigue_model.pkl")

ml_engine = MLEngine(model_path=MODEL_PATH)
ml_lock = threading.Lock()

last_ml_time = 0
cached_prediction = {"status": "Waiting...", "confidence": 0.0}
ML_INTERVAL = 0.5

@api_bp.route('/')
def home():
    return "✅ Flask Sensor + PERCLOS + Head Position (Wired Mode)", 200

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "timestamp": int(time.time()), 
        "service": "fatiguered-backend"
    }), 200

@api_bp.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    if latest_sensor_data["temperature"] is None:
        return jsonify({"message": "No data yet"}), 200
    return jsonify(latest_sensor_data), 200

@api_bp.route('/sensor_data/history', methods=['GET'])
def get_sensor_data_history():
    return jsonify(list(sensor_data_history)), 200

@api_bp.route('/head_position', methods=['GET'])
def get_head_position():
    """
    Returns head position solely based on SENSORS (Arduino).
    """
    ax = latest_sensor_data["ax"]
    ay = latest_sensor_data["ay"]
    az = latest_sensor_data["az"]

    if ax is None or ay is None or az is None:
        return jsonify({"position": "Unknown", "angle_x": 0, "angle_y": 0, "angle_z": 0}), 200

    # Sensor Calculation: (Unchanged - Arduino specific)
    pos, ang_x, ang_y, ang_z = calculate_head_position(ax, ay, az)

    head_position_data.update({
        "position": pos,
        "angle_x": round(ang_x, 2),
        "angle_y": round(ang_y, 2),
        "angle_z": round(ang_z, 2),
        "timestamp": int(time.time())
    })
    return jsonify(head_position_data), 200

@api_bp.route('/process_frame', methods=['POST'])
def process_frame():
    try:
        data = request.get_json()
        if not data or 'image_data' not in data:
            return jsonify({"error": "Missing image_data"}), 400

        base64_string = data['image_data'].split(',')[1]
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(base64_string), np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid frame data")

        frame = cv2.flip(frame, 1)
        result = process_face_mesh(frame)
        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@api_bp.route('/perclos', methods=['GET'])
def get_perclos():
    return jsonify(perclos_data), 200

@api_bp.route('/combined_data', methods=['GET'])
def get_combined_data():
    hp = {
        "position": "Unknown",
        "angle_x": 0.0,
        "angle_y": 0.0,
        "angle_z": 0.0,
        "timestamp": int(time.time()),
        "source": "None"
    }

    # CHECK FALLBACK LOGIC
    current_time = time.time()
    sensor_active = (
        latest_sensor_data.get("timestamp") is not None and 
        (current_time - latest_sensor_data["timestamp"] < 2.0) and
        latest_sensor_data.get("ax") is not None
    )

    if sensor_active:
        # 1. USE SENSOR (ARDUINO)
        pos, ang_x, ang_y, ang_z = calculate_head_position(
            latest_sensor_data["ax"],
            latest_sensor_data["ay"],
            latest_sensor_data["az"]
        )
        hp = {
            "position": pos,
            "angle_x": round(ang_x, 2),
            "angle_y": round(ang_y, 2),
            "angle_z": round(ang_z, 2),
            "timestamp": int(time.time()),
            "source": "Sensor"
        }
    else:
        # 2. USE CV (FALLBACK)
        with cv_angles_lock:
            # OpenCV Standard:
            # Pitch: +ve Look Down, -ve Look Up
            # Yaw: +ve Look Right, -ve Look Left
            # Roll: +ve Tilt Right, -ve Tilt Left
            
            c_pitch = cv_head_angles["pitch"]
            c_yaw = cv_head_angles["yaw"]
            c_roll = cv_head_angles["roll"]
            
            # Labeling Logic (Standard)
            v_label = ""
            if c_pitch > 10: v_label = "Down" 
            elif c_pitch < -10: v_label = "Up"
            
            h_label = ""
            if c_yaw > 10: h_label = "Right" 
            elif c_yaw < -10: h_label = "Left"
            
            pos_label = f"{v_label} {h_label}".strip()
            
            # Reset center if small angles
            if not pos_label:
                pos_label = "Center"

            hp = {
                "position": pos_label,
                "angle_x": round(c_pitch, 2),
                "angle_y": round(c_yaw, 2),
                "angle_z": round(c_roll, 2), 
                "timestamp": int(time.time()),
                "source": "Vision (Fallback)",
                "calibrated": cv_head_angles.get("is_calibrated", False)
            }

    global last_ml_time, cached_prediction
    
    # Rate-Limited ML Inference
    prediction_result = cached_prediction
    
    if (current_time - last_ml_time) > ML_INTERVAL:
        with ml_lock:
            if (time.time() - last_ml_time) > ML_INTERVAL:
                safe_sensor = {
                    "hr": latest_sensor_data.get("hr") or 0.0,
                    "temperature": latest_sensor_data.get("temperature") or 0.0,
                    "timestamp": latest_sensor_data.get("timestamp") or time.time()
                }
                
                prediction_result = ml_engine.predict(safe_sensor, {
                    **perclos_data,
                    "head_angle_x": hp["angle_x"],
                    "head_angle_y": hp["angle_y"]
                })
                cached_prediction = prediction_result
                last_ml_time = time.time()

    return jsonify({
        "sensor": latest_sensor_data,
        "perclos": perclos_data,
        "head_position": hp,
        "prediction": cached_prediction,
        "server_time": int(time.time())
    }), 200

@api_bp.route('/reset_calibration', methods=['POST'])
def reset_calibration():
    try:
        with ml_lock:
            ml_engine.reset_calibration()
            
            # Also reset vision calibration if it exists
            with cv_angles_lock:
                 cv_head_angles["is_calibrated"] = False
                 
            # Reset Eye Calibration
            from cv.perclos import reset_eye_calibration as reset_eyes
            reset_eyes()
                 
        return jsonify({"message": "Calibration reset successfully", "status": "OK"}), 200
    except Exception as e:
         return jsonify({"error": str(e)}), 500

@api_bp.route('/sensor_data/ingest', methods=['POST'])
def ingest_sensor_data():
    """
    Receives raw sensor string from local bridge (bridge.py)
    """
    try:
        data = request.get_json()
        raw_string = data.get("raw_sensor_data", "")
        
        if not raw_string:
            return jsonify({"error": "No data provided"}), 400

        from sensors.serial_reader import parse_raw_sensor_string
        
        parsed = parse_raw_sensor_string(raw_string)
        if parsed:
            timestamp = int(time.time())
            # Update Global State
            from sensors.serial_reader import latest_sensor_data, sensor_data_history
            
            # Use lock if needed (though Python GIL often handles dict updates nicely)
            # Importing lock would be better but keeping it simple for now
            latest_sensor_data.update({**parsed, "timestamp": timestamp})
            sensor_data_history.append(latest_sensor_data.copy())
            
            return jsonify({"status": "received", "data": parsed}), 200
        else:
            return jsonify({"status": "ignored", "reason": "parsing failed"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
