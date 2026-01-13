"""
API routes for sensor data, video processing, and ML predictions.
Migrated to FastAPI.
"""
import logging
import time
import base64
import cv2
import numpy as np
import threading
import traceback
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from config import get_config
from cv.perclos import process_face_mesh, perclos_data, reset_eye_calibration
from cv.head_pose import cv_head_angles, cv_angles_lock
from sensors.serial_reader import latest_sensor_data, sensor_data_history, head_position_data, calculate_head_position, sensor_lock
from ml.ml_engine import MLEngine

logger = logging.getLogger(__name__)
config = get_config()

router = APIRouter()

# --- Pydantic Models ---
class FrameData(BaseModel):
    image_data: str

class SensorIngest(BaseModel):
    raw_sensor_data: str

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

@router.get('/')
async def home():
    logger.info("Home endpoint accessed")
    return "✅ FastAPI Sensor + PERCLOS + Head Position (Wired Mode)"

@router.get('/health')
async def health_check():
    return {
        "status": "ok",
        "timestamp": int(time.time()), 
        "service": "fatiguered-backend"
    }

@router.get('/sensor_data')
async def get_sensor_data():
    with sensor_lock:
        if latest_sensor_data["temperature"] is None:
            logger.debug("No sensor data available yet")
            return {"message": "No data yet"}
        data = latest_sensor_data.copy()
    return data

@router.get('/sensor_data/history')
async def get_sensor_data_history():
    return list(sensor_data_history)

@router.get('/head_position')
async def get_head_position():
    """
    Returns head position solely based on SENSORS (Arduino).
    """
    ax = latest_sensor_data["ax"]
    ay = latest_sensor_data["ay"]
    az = latest_sensor_data["az"]

    if ax is None or ay is None or az is None:
        return {"position": "Unknown", "angle_x": 0, "angle_y": 0, "angle_z": 0}

    # Sensor Calculation: (Unchanged - Arduino specific)
    pos, ang_x, ang_y, ang_z = calculate_head_position(ax, ay, az)

    head_position_data.update({
        "position": pos,
        "angle_x": round(ang_x, 2),
        "angle_y": round(ang_y, 2),
        "angle_z": round(ang_z, 2),
        "timestamp": int(time.time())
    })
    return head_position_data

@router.post('/process_frame')
async def process_frame(data: FrameData):
    try:
        base64_string = data.image_data.split(',')[1] if ',' in data.image_data else data.image_data
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(base64_string), np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            logger.warning("Invalid frame data received")
            raise HTTPException(status_code=400, detail="Invalid frame data")

        frame = cv2.flip(frame, 1)
        result = process_face_mesh(frame)
        return result

    except Exception as e:
        logger.error(f"Error processing frame: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/perclos')
async def get_perclos():
    return perclos_data

@router.get('/combined_data')
async def get_combined_data():
    global last_ml_time, cached_prediction
    
    if ml_engine is None:
        logger.warning("ML Engine not available")
        raise HTTPException(status_code=503, detail="ML Engine not initialized")
    
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
    
    return {
        "sensor": sensor_data,
        "perclos": perclos_data,
        "head_position": hp,
        "prediction": prediction_result,
        "server_time": int(time.time()),
        "system_status": "Initializing" if is_calibrating else "Active"
    }

@router.post('/reset_calibration')
async def reset_calibration():
    try:
        with ml_lock:
            ml_engine.reset_calibration()
            reset_eye_calibration()
            
            # Also reset vision calibration if it exists
            with cv_angles_lock:
                 cv_head_angles["is_calibrated"] = False
        
        logger.info("Calibration reset successfully")
        return {"message": "Calibration reset successfully", "status": "OK"}
    except Exception as e:
        logger.error(f"Error resetting calibration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/sensor_data/ingest')
async def ingest_sensor_data(data: SensorIngest):
    """
    Receives raw sensor string from local bridge (bridge.py)
    """
    try:
        raw_string = data.raw_sensor_data
        
        if not raw_string:
            logger.warning("Sensor data ingest called without raw_sensor_data")
            raise HTTPException(status_code=400, detail="No data provided")

        from sensors.serial_reader import parse_raw_sensor_string
        
        parsed = parse_raw_sensor_string(raw_string)
        if parsed:
            timestamp = int(time.time())
            with sensor_lock:
                latest_sensor_data.update({**parsed, "timestamp": timestamp})
                sensor_data_history.append(latest_sensor_data.copy())
            
            logger.debug(f"Sensor data ingested: {parsed}")
            return {"status": "received", "data": parsed}
        else:
            logger.debug("Sensor data parsing failed")
            return {"status": "ignored", "reason": "parsing failed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting sensor data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/detect")
async def websocket_detect(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    try:
        while True:
            # Receive message (expecting base64 image data)
            data = await websocket.receive_text()
            
            try:
                 # Logic similar to process_frame
                base64_string = data.split(',')[1] if ',' in data else data
                frame = cv2.imdecode(np.frombuffer(base64.b64decode(base64_string), np.uint8), cv2.IMREAD_COLOR)
                
                if frame is None:
                    await websocket.send_json({"error": "Invalid frame"})
                    continue

                frame = cv2.flip(frame, 1)
                
                # We can return just perclos data or full data? Use process_face_mesh
                result = process_face_mesh(frame)
                
                # Send result back
                await websocket.send_json(result)
                
            except Exception as e:
                logger.error(f"WS Process Error: {e}")
                await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
