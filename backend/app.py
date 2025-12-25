
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import mediapipe as mp
import math
import time
from collections import deque
import numpy as np
import traceback
import base64
import threading
import serial
import serial.tools.list_ports
from ml_engine import MLEngine  # Import ML Engine

print("[DIAGNOSTIC] Environment OK ✅")

app = Flask(__name__)
CORS(app)
sensor_lock = threading.Lock()
ml_lock = threading.Lock()

# Initialize ML Engine
ml_engine = MLEngine(model_path="fatigue_model.pkl")

# ML Rate Limiting
last_ml_time = 0
cached_prediction = {"status": "Waiting...", "confidence": 0.0}
ML_INTERVAL = 0.5  # Run ML max every 0.5 seconds

latest_sensor_data = {
    "temperature": None,
    "ax": None, "ay": None, "az": None,
    "gx": None, "gy": None, "gz": None,
    "hr": None, "spo2": None,
    "timestamp": None
}
sensor_data_history = deque(maxlen=50)

head_position_data = {
    "position": "Center",
    "angle_x": 0.0,  # up-down
    "angle_y": 0.0,  # left-right
    "timestamp": int(time.time())
}

perclos_data = {
    "status": "No Face",
    "perclos": 0.0,
    "ear": 0.0,
    "yawn_status": "Closed",
    "mar": 0.0,
    "adaptive_mar_thresh": 0.6,
    "timestamp": int(time.time())
}

# CV Fallback Data
cv_head_angles = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}
cv_angles_lock = threading.Lock()

def calculate_cv_head_pose(landmarks, img_w, img_h):
    # 3D model points
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye left corner
        (225.0, 170.0, -135.0),      # Right eye right corner
        (-150.0, -150.0, -125.0),    # Left Mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ])

    # 2D image points (indices: 1, 152, 33, 263, 61, 291)
    # MediaPipe uses normalized coordinates
    points_idx = [1, 152, 33, 263, 61, 291]
    image_points = np.array([
        (landmarks[i].x * img_w, landmarks[i].y * img_h) 
        for i in points_idx
    ], dtype="double")

    focal_length = img_w
    center = (img_w / 2, img_h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")
    dist_coeffs = np.zeros((4, 1))

    success, rotation_vector, translation_vector = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0, 0, 0
    
    # Get Euler Angles
    rmat, _ = cv2.Rodrigues(rotation_vector)
    # RQDecomp3x3 returns (mtxR, mtxQ, Qx, Qy, Qz) where mtxR contains Euler angles?
    # actually typically: angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
    angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
    
    # Scaling to match expected degrees
    # RQDecomp3x3 returns angles in degrees directly
    pitch = angles[0]
    yaw = angles[1]
    roll = angles[2]
    
    return pitch, yaw, roll

def parse_raw_sensor_string(raw: str):

    parts = [p.strip() for p in raw.split(',') if p.strip()]
    parsed = {}
    for p in parts:
        if ':' not in p:
            continue
        k, v = p.split(':', 1)
        k, v = k.lower(), v.strip()
        try:
            if k in ("t", "temperature"):
                parsed["temperature"] = float(v)
            elif k in ("hr", "bpm", "heart_rate"):
                parsed["hr"] = float(v)
            elif k in ("spo2", "sp02"):
                parsed["spo2"] = float(v)
            elif k in ("ax", "ay", "az", "gx", "gy", "gz"):
                parsed[k] = float(v)
        except ValueError:
            continue
    return parsed


def find_arduino_port():
    # FORCE COM6 for now (User confirmed it exists)
    return "COM6"

def serial_reader():
    global latest_sensor_data, sensor_data_history
    try:
        port = find_arduino_port()
        # Open Serial Port
        ser = serial.Serial(port=port, baudrate=115200, timeout=1)
        print(f"[SERIAL] ✅ Connected to {port}")
        
        while True:
            try:
                # Read line
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                        
                    print(f"\n[ARDUINO RAW] >>> {line}")  # Explicitly show data
                    
                    parsed = parse_raw_sensor_string(line)
                    if not parsed:
                        continue

                    timestamp = int(time.time())
                    with sensor_lock:
                        latest_sensor_data.update({**parsed, "timestamp": timestamp})
                        sensor_data_history.append(latest_sensor_data.copy())

            except Exception as loop_e:
                print(f"[SERIAL LOOP ERROR] {loop_e}")
                time.sleep(1)

    except Exception as e:
        print(f"[SERIAL CONNECTION ERROR] {e}")
        traceback.print_exc()

@app.route('/')
def home():
    return "✅ Flask Sensor + PERCLOS + Head Position (Wired Mode)", 200


@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    if latest_sensor_data["temperature"] is None:
        return jsonify({"message": "No data yet"}), 200
    return jsonify(latest_sensor_data), 200


@app.route('/sensor_data/history', methods=['GET'])
def get_sensor_data_history():
    return jsonify(list(sensor_data_history)), 200

def calculate_head_position(ax, ay, az):

    try:
        # PITCH (Up/Down) - Rotation around X-axis
        # atan2(x, sqrt(y*y + z*z))
        # Reverted per user request (Keep Up/Down Same)
        angle_x = math.degrees(math.atan2(ax, math.sqrt(ay**2 + az**2)))
        
        # YAW (Left/Right) - Rotation around Y-axis
        # atan2(y, sqrt(x*x + z*z))
        # Reverted to Normal (No Inversion)
        angle_y = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
        
        # ROLL (Tilt Left/Right) - Rotation around Z-axis
        # atan2(y, z) is the standard approximation for roll from accelerometer
        angle_z = math.degrees(math.atan2(ay, az))   

        UP_THRESHOLD = 10
        DOWN_THRESHOLD = -10
        LEFT_THRESHOLD = -10
        RIGHT_THRESHOLD = 10

        if angle_x > UP_THRESHOLD:
            vertical = "Up"
        elif angle_x < DOWN_THRESHOLD:
            vertical = "Down"
        else:
            vertical = "Center"

        if angle_y > RIGHT_THRESHOLD:
            horizontal = "Right"
        elif angle_y < LEFT_THRESHOLD:
            horizontal = "Left"
        else:
            horizontal = "Center"
            
        if vertical == "Center" and horizontal == "Center":
            position = "Center"
        elif vertical != "Center" and horizontal == "Center":
            position = vertical
        elif horizontal != "Center" and vertical == "Center":
            position = horizontal
        else:
            position = f"{vertical}-{horizontal}"

        return position, angle_x, angle_y, angle_z

    except Exception as e:
        print(f"[HEAD POSITION ERROR] {e}")
        return "Unknown", 0.0, 0.0, 0.0



@app.route('/head_position', methods=['GET'])
def get_head_position():
    ax = latest_sensor_data["ax"]
    ay = latest_sensor_data["ay"]
    az = latest_sensor_data["az"]

    if ax is None or ay is None or az is None:
        return jsonify({"position": "Unknown", "angle_x": 0, "angle_y": 0, "angle_z": 0}), 200

    pos, ang_x, ang_y, ang_z = calculate_head_position(ax, ay, az)

    head_position_data.update({
        "position": pos,
        "angle_x": round(ang_x, 2),
        "angle_y": round(ang_y, 2),
        "angle_z": round(ang_z, 2),
        "timestamp": int(time.time())
    })
    return jsonify(head_position_data), 200


# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
EYE_AR_THRESH = 0.25
MOUTH_INNER = [13, 14, 78, 308]
MAR_THRESH = 0.6
MAR_FRAME_COUNT = 3

eye_status_history = deque(maxlen=6)
yawn_frames_count = 0
mar_history = deque(maxlen=20)


def eye_aspect_ratio(eye):
    if len(eye) != 6:
        return 0
    A = math.dist(eye[1], eye[5])
    B = math.dist(eye[2], eye[4])
    C = math.dist(eye[0], eye[3])
    return (A + B) / (2.0 * C) if C else 0


def mouth_aspect_ratio(mouth):
    if len(mouth) != 4:
        return 0
    v = math.dist(mouth[0], mouth[1])
    h = math.dist(mouth[2], mouth[3])
    return v / h if h else 0


@app.route('/process_frame', methods=['POST'])
def process_frame():
    global perclos_data, eye_status_history, yawn_frames_count, mar_history
    now = int(time.time())

    try:
        data = request.get_json()
        if not data or 'image_data' not in data:
            return jsonify({"error": "Missing image_data"}), 400

        base64_string = data['image_data'].split(',')[1]
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(base64_string), np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid frame data")

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        h, w, _ = frame.shape

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0]
            
            # --- CV HEAD POSE FALLBACK ---
            try:
                cv_pitch, cv_yaw, cv_roll = calculate_cv_head_pose(lm.landmark, w, h)
                with cv_angles_lock:
                    cv_head_angles["pitch"] = cv_pitch
                    cv_head_angles["yaw"] = cv_yaw
                    cv_head_angles["roll"] = cv_roll
            except Exception as cv_e:
                print(f"[CV POSE ERROR] {cv_e}")

            left = [(lm.landmark[i].x * w, lm.landmark[i].y * h) for i in LEFT_EYE]
            right = [(lm.landmark[i].x * w, lm.landmark[i].y * h) for i in RIGHT_EYE]
            ear = (eye_aspect_ratio(left) + eye_aspect_ratio(right)) / 2
            eyes_closed = 1 if ear < EYE_AR_THRESH else 0
            eye_status_history.append(eyes_closed)
            perclos_val = (sum(eye_status_history) / len(eye_status_history)) * 100

            mouth = [(lm.landmark[i].x * w, lm.landmark[i].y * h) for i in MOUTH_INNER]
            mar = mouth_aspect_ratio(mouth)
            if mar > 0:
                mar_history.append(mar)
            mean_mar = np.mean(mar_history) if mar_history else 0.0
            adaptive_thresh = max(MAR_THRESH, mean_mar * 1.3) if mean_mar > 0 else MAR_THRESH

            if mar > adaptive_thresh:
                yawn_frames_count += 1
                yawn_status = "Yawning" if yawn_frames_count >= MAR_FRAME_COUNT else "Opening"
            else:
                yawn_frames_count = max(0, yawn_frames_count - 1)
                yawn_status = "Closed" if yawn_frames_count == 0 else "Relaxing"

            perclos_data.update({
                "status": "Closed" if eyes_closed else "Open",
                "perclos": round(perclos_val, 1),
                "ear": round(ear, 3),
                "yawn_status": yawn_status,
                "mar": round(mar, 3),
                "adaptive_mar_thresh": round(adaptive_thresh, 3),
                "timestamp": now
            })
        else:
            eye_status_history.clear()
            yawn_frames_count = 0
            mar_history.clear()
            perclos_data.update({
                "status": "No Face",
                "perclos": 0.0,
                "ear": 0.0,
                "yawn_status": "No Face",
                "mar": 0.0,
                "adaptive_mar_thresh": MAR_THRESH,
                "timestamp": now
            })

        return jsonify(perclos_data), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/perclos', methods=['GET'])
def get_perclos():
    return jsonify(perclos_data), 200


@app.route('/combined_data', methods=['GET'])
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
            # OpenCV PnP: 
            # Pitch (X): +ve is DOWN, -ve is UP (usually) -> We invert for UI if UI expects +ve Up
            # Yaw (Y): +ve is Right, -ve is Left
            # Roll (Z): +ve is Tilt Right
            
            c_pitch = cv_head_angles["pitch"]  # Revert Inversion (Requested Reverse All)
            c_yaw = cv_head_angles["yaw"]      # Revert Inversion (Requested Reverse All)
            c_roll = cv_head_angles["roll"]
            
            # Heuristic Labeling for CV (Combined Directions)
            v_label = ""
            if c_pitch > 10: v_label = "Up"
            elif c_pitch < -10: v_label = "Down"
            
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
                "angle_z": round(c_roll, 2), # Use corrected roll
                "timestamp": int(time.time()),
                "source": "Vision (Fallback)"
            }

    global last_ml_time, cached_prediction
    
    # Rate-Limited ML Inference
    prediction_result = cached_prediction
    
    # Only run expensive ML if enough time passed
    if (current_time - last_ml_time) > ML_INTERVAL:
        with ml_lock:
            # Check again inside lock
            if (time.time() - last_ml_time) > ML_INTERVAL:
                # Sanitize Data (Ensure no NoneTypes)
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


# ------------------ RUN SERVER ------------------
if __name__ == '__main__':
    serial_thread = threading.Thread(target=serial_reader, daemon=True)
    serial_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
