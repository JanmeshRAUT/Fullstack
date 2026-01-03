"""
API routes for sensor data, video processing, and ML predictions.
"""
import logging
import time
import base64
import cv2
import numpy as np
import threading
import traceback
from flask import Blueprint, jsonify, request

from config import get_config
from cv.perclos import process_face_mesh, perclos_data, reset_eye_calibration
from cv.head_pose import cv_head_angles, cv_angles_lock
from sensors.serial_reader import latest_sensor_data, sensor_data_history, head_position_data, calculate_head_position, sensor_lock
from ml.ml_engine import MLEngine

logger = logging.getLogger(__name__)
config = get_config()

api_bp = Blueprint('api', __name__)

# --- ML Engine & State ---
try:
    ml_engine = MLEngine(model_path=config.MODEL_PATH)
    logger.info("ML Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ML Engine: {e}", exc_info=True)
    ml_engine = None

ml_lock = threading.Lock()

last_ml_time = 0
cached_prediction = {"status": "Waiting...", "confidence": 0.0}
ML_INTERVAL = config.ML_INTERVAL

@api_bp.route('/')
def home():
    logger.info("Home endpoint accessed")
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
    with sensor_lock:
        if latest_sensor_data["temperature"] is None:
            logger.debug("No sensor data available yet")
            return jsonify({"message": "No data yet"}), 200
        data = latest_sensor_data.copy()
    return jsonify(data), 200

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
            logger.warning("Process frame called without image_data")
            return jsonify({"error": "Missing image_data"}), 400

        base64_string = data['image_data'].split(',')[1]
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(base64_string), np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            logger.warning("Invalid frame data received")
            raise ValueError("Invalid frame data")

        frame = cv2.flip(frame, 1)
        result = process_face_mesh(frame)
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error processing frame: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@api_bp.route('/perclos', methods=['GET'])
def get_perclos():
    return jsonify(perclos_data), 200

@api_bp.route('/combined_data', methods=['GET'])
def get_combined_data():
    global last_ml_time, cached_prediction
    
    if ml_engine is None:
        logger.warning("ML Engine not available")
        return jsonify({"error": "ML Engine not initialized"}), 503
    
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
    
    with sensor_lock:
        sensor_active = (
            latest_sensor_data.get("timestamp") is not None and 
            (current_time - latest_sensor_data["timestamp"] < config.SENSOR_TIMEOUT) and
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

    if not sensor_active:
        # 2. USE CV (FALLBACK)
        with cv_angles_lock:
            c_pitch = cv_head_angles["pitch"]
            c_yaw = cv_head_angles["yaw"]
            c_roll = cv_head_angles["roll"]
            
            v_label = ""
            if c_pitch > 10: v_label = "Down" 
            elif c_pitch < -10: v_label = "Up"
            
            h_label = ""
            if c_yaw > 10: h_label = "Right" 
            elif c_yaw < -10: h_label = "Left"
            
            pos_label = f"{v_label} {h_label}".strip()
            
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

    # Rate-Limited ML Inference
    prediction_result = cached_prediction
    
    is_calibrating = perclos_data.get("is_calibrating", False)
    if is_calibrating:
        prediction_result = {"status": "Initializing...", "confidence": 0.0}

    if (current_time - last_ml_time) > ML_INTERVAL and not is_calibrating:
        with ml_lock:
            if (time.time() - last_ml_time) > ML_INTERVAL:
                with sensor_lock:
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

    with sensor_lock:
        sensor_data = latest_sensor_data.copy()
    
    return jsonify({
        "sensor": sensor_data,
        "perclos": perclos_data,
        "head_position": hp,
        "prediction": prediction_result,
        "server_time": int(time.time()),
        "system_status": "Initializing" if is_calibrating else "Active"
    }), 200

@api_bp.route('/reset_calibration', methods=['POST'])
def reset_calibration():
    try:
        with ml_lock:
            ml_engine.reset_calibration()
            reset_eye_calibration()
            
            # Also reset vision calibration if it exists
            with cv_angles_lock:
                 cv_head_angles["is_calibrated"] = False
        
        logger.info("Calibration reset successfully")
        return jsonify({"message": "Calibration reset successfully", "status": "OK"}), 200
    except Exception as e:
        logger.error(f"Error resetting calibration: {e}", exc_info=True)
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
            logger.warning("Sensor data ingest called without raw_sensor_data")
            return jsonify({"error": "No data provided"}), 400

        from sensors.serial_reader import parse_raw_sensor_string
        
        parsed = parse_raw_sensor_string(raw_string)
        if parsed:
            timestamp = int(time.time())
            with sensor_lock:
                latest_sensor_data.update({**parsed, "timestamp": timestamp})
                sensor_data_history.append(latest_sensor_data.copy())
            
            logger.debug(f"Sensor data ingested: {parsed}")
            return jsonify({"status": "received", "data": parsed}), 200
        else:
            logger.debug("Sensor data parsing failed")
            return jsonify({"status": "ignored", "reason": "parsing failed"}), 200

    except Exception as e:
        logger.error(f"Error ingesting sensor data: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
