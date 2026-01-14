import logging
import time
import base64
import cv2
import numpy as np
import asyncio
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import get_config
from cv.perclos import process_face_mesh, perclos_data, reset_eye_calibration
from cv.head_pose import cv_head_angles, cv_angles_lock
from sensors.serial_reader import start_serial_thread, latest_sensor_data, sensor_data_history, head_position_data, calculate_head_position, sensor_lock, parse_raw_sensor_string
from ml.ml_engine import MLEngine

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FastAPI")

config = get_config()

# Global ML Engine
ml_engine = None
ml_lock = threading.Lock()
last_ml_time = 0
cached_prediction = {"status": "Waiting...", "confidence": 0.0}
ML_INTERVAL = config.ML_INTERVAL

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting FastAPI Server...")
    
    # Initialize Serial Thread
    start_serial_thread()
    
    # Initialize ML Engine
    global ml_engine
    try:
        ml_engine = MLEngine(model_path=config.MODEL_PATH)
        logger.info("✅ ML Engine Initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ML Engine: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Stopping FastAPI Server...")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    raw_sensor_data: str

@app.get("/")
async def root():
    return "✅ FastAPI Sensor + PERCLOS + Head Position (WebSockets Active)"

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": int(time.time()),
        "service": "fatiguered-backend-fastapi"
    }

# --- WEB SOCKET ENDPOINT ---
@app.websocket("/ws/detect")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket Client Connected")
    # --- OPTIMIZATION: FRAME SKIPPING ---
    frame_counter = 0
    PROCESS_EVERY_N_FRAMES = 3  # Analyze only 1 out of 3 frames (reduces load by ~66%)
    
    try:
        while True:
            # Receive frame data
            data = await websocket.receive_json()
            
            if "image_data" not in data:
                continue

            frame_counter += 1
            should_process = (frame_counter % PROCESS_EVERY_N_FRAMES == 0)

            if should_process:
                # Decode Image only when needed
                try:
                    base64_string = data['image_data'].split(',')[1]
                    frame_bytes = base64.b64decode(base64_string)
                    np_arr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        frame = cv2.flip(frame, 1)
                        # --- PROCESS FRAME (Perclos + Head Pose) ---
                        # This function updates global perclos_data internally
                        process_face_mesh(frame)
                        
                except Exception as e:
                    logger.error(f"Error processing frame in WS: {e}")
            
            # --- COMBINE DATA FOR RESPONSE ---
            # Even if we skipped vision processing, we return the latest Sensor Data + cached Vision Data
            response_data = await get_combined_data_internal()
            
            # Send back processed data
            await websocket.send_json(response_data)
                
    except WebSocketDisconnect:
        logger.info("WebSocket Client Disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")

# --- INTERNAL HELPER ---
async def get_combined_data_internal():
    global last_ml_time, cached_prediction
    
    hp = {
        "position": "Unknown",
        "angle_x": 0.0,
        "angle_y": 0.0,
        "angle_z": 0.0,
        "timestamp": int(time.time()),
        "source": "None"
    }
    
    current_time = time.time()
    
    # SENSOR / HEAD POSE LOGIC
    with sensor_lock:
        sensor_active = (
            latest_sensor_data.get("timestamp") is not None and 
            (current_time - latest_sensor_data["timestamp"] < config.SENSOR_TIMEOUT) and
            latest_sensor_data.get("ax") is not None
        )
        
        if sensor_active:
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
            if not pos_label: pos_label = "Center"

            hp = {
                "position": pos_label,
                "angle_x": round(c_pitch, 2),
                "angle_y": round(c_yaw, 2),
                "angle_z": round(c_roll, 2),
                "timestamp": int(time.time()),
                "source": "Vision (Fallback)",
                "calibrated": cv_head_angles.get("is_calibrated", False)
            }

    # ML PREDICTION
    prediction_result = cached_prediction
    is_calibrating = perclos_data.get("is_calibrating", False)
    
    if is_calibrating:
        prediction_result = {"status": "Initializing...", "confidence": 0.0}
    
    # Check ML Interval
    if (current_time - last_ml_time) > ML_INTERVAL and not is_calibrating and ml_engine:
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
        sensor_data_snap = latest_sensor_data.copy()

    return {
        "sensor": sensor_data_snap,
        "perclos": perclos_data,
        "head_position": hp,
        "prediction": prediction_result,
        "server_time": int(time.time()),
        "system_status": "Initializing" if is_calibrating else "Active"
    }

# --- REST ENDPOINTS (Legacy/Polling) ---
@app.get("/api/combined_data")
async def get_combined_data():
    return await get_combined_data_internal()

@app.get("/api/sensor_data")
async def get_sensor_data():
    with sensor_lock:
        data = latest_sensor_data.copy()
    return data

@app.get("/api/sensor_data/history")
async def get_sensor_data_history():
    return list(sensor_data_history)

@app.post("/api/reset_calibration")
async def reset_calibration_endpoint():
    try:
        with ml_lock:
            if ml_engine:
                ml_engine.reset_calibration()
            reset_eye_calibration()
            with cv_angles_lock:
                 cv_head_angles["is_calibrated"] = False
        return {"message": "Calibration reset successfully", "status": "OK"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/sensor_data/ingest")
async def ingest_sensor_data(item: IngestRequest):
    try:
        raw_string = item.raw_sensor_data
        if not raw_string:
             return JSONResponse(status_code=400, content={"error": "No data provided"})
        
        parsed = parse_raw_sensor_string(raw_string)
        if parsed:
            timestamp = int(time.time())
            with sensor_lock:
                latest_sensor_data.update({**parsed, "timestamp": timestamp})
                sensor_data_history.append(latest_sensor_data.copy())
            return {"status": "received", "data": parsed}
        else:
            return {"status": "ignored", "reason": "parsing failed"}
    except Exception as e:
        logger.error(f"Error ingesting: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    # Use 'server:app' if running via command line, but here we run app directly
    uvicorn.run(app, host="0.0.0.0", port=5000)
