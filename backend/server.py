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
import io
import threading

try:
    print("[DIAGNOSTIC] Basic environment check successful.")
except Exception as e:
    print(f"[CRITICAL ERROR] Dependency check failed. Error: {e}")

app = Flask(__name__)
CORS(app)

# ------------------ Globals & Locks ------------------
sensor_lock = threading.Lock()

latest_sensor_data = {
    "temperature": None,
    "ax": None, "ay": None, "az": None,
    "gx": None, "gy": None, "gz": None,
    "hr": None, "spo2": None,
    "timestamp": None
}
sensor_data_history = deque(maxlen=50)  # keep more history

head_position_data = {
    "position": "Center",
    "angle": 0.0,
    "timestamp": int(time.time())
}

# perclos_data (keeps your existing fields)
perclos_data = {
    "status": "No Face",
    "perclos": 0.0,
    "ear": 0.0,
    "yawn_status": "Closed",
    "mar": 0.0,
    "adaptive_mar_thresh": 0.6,
    "timestamp": int(time.time())
}

# ------------------ Helpers ------------------
def parse_raw_sensor_string(raw: str):
    """
    Parse strings like:
    "T:30.94,HR:72,SpO2:98,AX:-0.71,AY:0.62,AZ:-0.06,GX:-3.23,GY:0.39,GZ:1.08"
    Returns dict with normalized lowercase keys: temperature, hr, spo2, ax, ay, az, gx, gy, gz
    """
    try:
        parts = [p.strip() for p in raw.split(',') if p.strip()]
        parsed = {}
        for p in parts:
            if ':' not in p:
                continue
            k, v = p.split(':', 1)
            k = k.strip().lower()
            v = v.strip()
            # normalize keys
            if k in ("t", "temperature"):
                parsed["temperature"] = float(v)
            elif k in ("hr", "bpm", "heart_rate", "heart-rate"):
                parsed["hr"] = float(v)
            elif k in ("spo2", "sp02", "sp_o2"):
                parsed["spo2"] = float(v)
            elif k in ("ax", "accel_x", "acc_x"):
                parsed["ax"] = float(v)
            elif k in ("ay", "accel_y", "acc_y"):
                parsed["ay"] = float(v)
            elif k in ("az", "accel_z", "acc_z"):
                parsed["az"] = float(v)
            elif k in ("gx", "gyro_x"):
                parsed["gx"] = float(v)
            elif k in ("gy", "gyro_y"):
                parsed["gy"] = float(v)
            elif k in ("gz", "gyro_z"):
                parsed["gz"] = float(v)
            else:
                # ignore unknown keys (or add as raw)
                try:
                    parsed[k] = float(v)
                except:
                    parsed[k] = v
        return parsed
    except Exception:
        raise

# ------------------ SENSOR DATA ENDPOINTS ------------------

@app.route('/')
def home():
    return "Flask Sensor + PERCLOS + Head Position Server Running", 200

@app.route('/sensor_data', methods=['POST'])
def post_sensor_data():
    """Accepts sensor packet from ESP (JSON or raw text) and stores latest"""
    global latest_sensor_data, sensor_data_history

    try:
        parsed = {}

        # 1) Try JSON first
        if request.is_json:
            parsed_json = request.get_json()
            # normalize keys to expected names
            normalized = {}
            for k, v in parsed_json.items():
                k_l = k.strip().lower()
                if k_l in ("temperature", "t"):
                    normalized["temperature"] = float(v)
                elif k_l in ("hr", "bpm", "heart_rate", "heart-rate"):
                    normalized["hr"] = float(v)
                elif k_l in ("spo2", "sp02", "sp_o2"):
                    normalized["spo2"] = float(v)
                elif k_l in ("ax", "accel_x", "acc_x"):
                    normalized["ax"] = float(v)
                elif k_l in ("ay", "accel_y", "acc_y"):
                    normalized["ay"] = float(v)
                elif k_l in ("az", "accel_z", "acc_z"):
                    normalized["az"] = float(v)
                elif k_l in ("gx", "gyro_x"):
                    normalized["gx"] = float(v)
                elif k_l in ("gy", "gyro_y"):
                    normalized["gy"] = float(v)
                elif k_l in ("gz", "gyro_z"):
                    normalized["gz"] = float(v)
                else:
                    try:
                        normalized[k_l] = float(v)
                    except:
                        normalized[k_l] = v
            parsed = normalized

        else:
            # 2) Raw text body
            raw = request.get_data(as_text=True).strip()
            if raw.startswith("data="):
                raw = raw[len("data="):]
            parsed = parse_raw_sensor_string(raw)

        # Ensure required keys exist
        required_keys = ["temperature", "ax", "ay", "az", "gx", "gy", "gz"]
        if not all(k in parsed for k in required_keys):
            if "temperature" not in parsed:
                return jsonify({"error": "Missing required sensor keys"}), 400

        # Store with lock
        timestamp = int(time.time())
        with sensor_lock:
            current = {
                "temperature": float(parsed.get("temperature")) if parsed.get("temperature") is not None else None,
                "ax": float(parsed.get("ax")) if parsed.get("ax") is not None else None,
                "ay": float(parsed.get("ay")) if parsed.get("ay") is not None else None,
                "az": float(parsed.get("az")) if parsed.get("az") is not None else None,
                "gx": float(parsed.get("gx")) if parsed.get("gx") is not None else None,
                "gy": float(parsed.get("gy")) if parsed.get("gy") is not None else None,
                "gz": float(parsed.get("gz")) if parsed.get("gz") is not None else None,
                "hr": float(parsed.get("hr")) if parsed.get("hr") is not None else None,
                "spo2": float(parsed.get("spo2")) if parsed.get("spo2") is not None else None,
                "timestamp": timestamp
            }
            latest_sensor_data.update(current)
            sensor_data_history.append(latest_sensor_data.copy())

        # Log properly
        print(
            f"[SENSOR] T:{latest_sensor_data['temperature']:.2f}°C, "
            f"HR:{(int(latest_sensor_data['hr']) if latest_sensor_data['hr'] is not None else 'NA')}, "
            f"SpO2:{(int(latest_sensor_data['spo2']) if latest_sensor_data['spo2'] is not None else 'NA')}, "
            f"A({latest_sensor_data['ax']:.2f},{latest_sensor_data['ay']:.2f},{latest_sensor_data['az']:.2f})g, "
            f"G({latest_sensor_data['gx']:.2f},{latest_sensor_data['gy']:.2f},{latest_sensor_data['gz']:.2f})",
            flush=True
        )

        return jsonify({"status": "success", "timestamp": timestamp}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    """Return latest sensor packet (including hr & spo2 if present)"""
    if latest_sensor_data["temperature"] is None:
        return jsonify({"message": "No data yet", "data": None}), 200
    return jsonify(latest_sensor_data), 200

@app.route('/sensor_data/history', methods=['GET'])
def get_sensor_data_history():
    """Return last N sensor packets"""
    return jsonify(list(sensor_data_history)), 200

# ------------------ HEAD POSITION ------------------
def calculate_head_position(ax, ay, az):
    try:
        angle_y = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
        LEFT_THRESHOLD = -5
        RIGHT_THRESHOLD = 5
        if angle_y > RIGHT_THRESHOLD:
            position = "Right"
        elif angle_y < LEFT_THRESHOLD:
            position = "Left"
        else:
            position = "Center"
        return position, angle_y
    except Exception as e:
        print(f"[HEAD POSITION ERROR] {e}", flush=True)
        return "Unknown", 0.0

@app.route('/head_position', methods=['GET'])
def get_head_position():
    global head_position_data
    if latest_sensor_data["ax"] is None:
        return jsonify({
            "message": "No sensor data yet",
            "data": None,
            "timestamp": int(time.time())
        }), 200
    try:
        ax, ay, az = latest_sensor_data["ax"], latest_sensor_data["ay"], latest_sensor_data["az"]
        position, angle = calculate_head_position(ax, ay, az)
        head_position_data = {
            "position": position,
            "angle": round(angle, 2),
            "timestamp": int(time.time())
        }
        print(f"[HEAD POSITION] {position} ({angle:.2f}°)", flush=True)
        return jsonify(head_position_data), 200
    except Exception as e:
        print(f"[HEAD POSITION ERROR] {e}", flush=True)
        traceback.print_exc()
        return jsonify({"error": "Head position calculation failed"}), 500

# ------------------ PERCLOS / FACE MESH (unchanged logic) ------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
EYE_AR_THRESH = 0.25
WINDOW_SIZE = 6

MOUTH_INNER = [13, 14, 78, 308]
MAR_THRESH = 0.6
MAR_FRAME_COUNT = 3

eye_status_history = deque(maxlen=WINDOW_SIZE)
yawn_frames_count = 0
mar_history = deque(maxlen=20)

def eye_aspect_ratio(eye):
    if len(eye) != 6:
        return 0.0
    A = math.dist(eye[1], eye[5])
    B = math.dist(eye[2], eye[4])
    C = math.dist(eye[0], eye[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)

def mouth_aspect_ratio(mouth):
    if len(mouth) != 4:
        return 0.0
    vertical_dist = math.dist(mouth[0], mouth[1])
    horizontal_dist = math.dist(mouth[2], mouth[3])
    if horizontal_dist == 0:
        return 0.0
    return vertical_dist / horizontal_dist

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Receives base64 image data from the frontend, processes it, and updates perclos_data."""
    global perclos_data, eye_status_history, yawn_frames_count, mar_history
    now = int(time.time())

    try:
        data = request.get_json()
        if not data or 'image_data' not in data:
            print("[FRAME ERROR] Missing image_data key.", flush=True)
            return jsonify({"error": "Missing image_data"}), 400

        base64_string = data['image_data'].split(',')[1]
        image_bytes = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_bytes, np.uint8)

        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Could not decode image data into OpenCV frame.")

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        h, w, _ = frame.shape

        current_ear = 0.0
        current_mar = 0.0
        yawn_status = "Closed"

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]

            left = [(landmarks.landmark[i].x * w, landmarks.landmark[i].y * h) for i in LEFT_EYE]
            right = [(landmarks.landmark[i].x * w, landmarks.landmark[i].y * h) for i in RIGHT_EYE]
            current_ear = (eye_aspect_ratio(left) + eye_aspect_ratio(right)) / 2.0
            eyes_closed = 1 if current_ear < EYE_AR_THRESH else 0
            eye_status_history.append(eyes_closed)
            perclos_val = (sum(eye_status_history) / max(1, len(eye_status_history))) * 100
            eye_status = "Closed" if eyes_closed else "Open"

            mouth = [(landmarks.landmark[i].x * w, landmarks.landmark[i].y * h) for i in MOUTH_INNER]
            current_mar = mouth_aspect_ratio(mouth)

            if current_mar > 0:
                mar_history.append(current_mar)

            mean_mar = float(np.mean(mar_history)) if len(mar_history) > 0 else 0.0
            adaptive_thresh = max(MAR_THRESH, mean_mar * 1.3) if mean_mar > 0 else MAR_THRESH

            if current_mar > adaptive_thresh:
                yawn_frames_count += 1
                if yawn_frames_count >= MAR_FRAME_COUNT:
                    yawn_status = "Yawning"
                else:
                    yawn_status = "Opening"
            else:
                yawn_frames_count = max(0, yawn_frames_count - 1)
                if yawn_frames_count >= MAR_FRAME_COUNT:
                    yawn_status = "Yawning"
                elif yawn_frames_count > 0:
                    yawn_status = "Relaxing"
                else:
                    yawn_status = "Closed"

            perclos_data = {
                "status": eye_status,
                "perclos": round(perclos_val, 1),
                "ear": round(current_ear, 3),
                "yawn_status": yawn_status,
                "mar": round(current_mar, 3),
                "adaptive_mar_thresh": round(adaptive_thresh, 3),
                "timestamp": now
            }

            print(
                f"[FRAME PROCESSED] Eye:{eye_status}, EAR={current_ear:.3f}, "
                f"Yawn:{yawn_status}, MAR={current_mar:.3f}, AdaptiveMAR={adaptive_thresh:.3f}, "
                f"PERCLOS={perclos_val:.1f}%",
                flush=True
            )
        else:
            eye_status_history.clear()
            yawn_frames_count = 0
            mar_history.clear()
            perclos_data = {
                "status": "No Face",
                "perclos": 0.0,
                "ear": 0.0,
                "yawn_status": "No Face",
                "mar": 0.0,
                "adaptive_mar_thresh": MAR_THRESH,
                "timestamp": now
            }
            print("[NO FACE] Waiting for face...", flush=True)

        return jsonify(perclos_data), 200

    except Exception as e:
        print(f"[PROCESSING ERROR] {e}", flush=True)
        traceback.print_exc()
        return jsonify({"error": "Frame processing failed"}), 500

@app.route('/perclos', methods=['GET'])
def get_perclos():
    """Return latest PERCLOS data"""
    return jsonify(perclos_data), 200

# ------------------ Combined Endpoint for Frontend ------------------
@app.route('/combined_data', methods=['GET'])
def get_combined_data():
    """
    Return a single JSON object with:
     - latest sensor (temperature, hr, spo2, accel, gyro)
     - perclos (face-based metrics)
     - head_position (Left/Center/Right)
    """
    # Compute head pos on the fly
    hp = {"position": "Unknown", "angle": 0.0, "timestamp": int(time.time())}
    if latest_sensor_data.get("ax") is not None:
        pos, ang = calculate_head_position(latest_sensor_data["ax"], latest_sensor_data["ay"], latest_sensor_data["az"])
        hp = {"position": pos, "angle": round(ang, 2), "timestamp": int(time.time())}

    response = {
        "sensor": latest_sensor_data,
        "perclos": perclos_data,
        "head_position": hp,
        "server_time": int(time.time())
    }
    return jsonify(response), 200

# ------------------ Run ------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
