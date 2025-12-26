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

try:
    print("[DIAGNOSTIC] Basic environment check successful.")
except Exception as e:
    print(f"[CRITICAL ERROR] Dependency check failed. Error: {e}")


app = Flask(__name__)
CORS(app) 

latest_sensor_data = {
    "temperature": None,
    "ax": None, "ay": None, "az": None,
    "gx": None, "gy": None, "gz": None,
    "timestamp": None
}
sensor_data_history = deque(maxlen=10)


@app.route('/')
def home():
    return "Flask Sensor + PERCLOS + Head Position Server Running", 200


@app.route('/sensor_data', methods=['POST'])
def post_sensor_data():

    global latest_sensor_data, sensor_data_history
    try:
        data = request.get_json()

        if data is None:
            raw = request.get_data(as_text=True)
            print(f"[CRITICAL DEBUG] Invalid JSON. Raw body: {raw}", flush=True) 
            return jsonify({"error": "Invalid JSON format"}), 400

        required_keys = ["temperature", "ax", "ay", "az", "gx", "gy", "gz"]
        if not all(k in data for k in required_keys):
            print(f"[VALIDATION ERROR] Missing keys: {data}", flush=True)
            return jsonify({"error": "Missing one or more required keys"}), 400

        timestamp = int(time.time())
        current = {
            "temperature": float(data["temperature"]),
            "ax": float(data["ax"]),
            "ay": float(data["ay"]),
            "az": float(data["az"]),
            "gx": float(data["gx"]),
            "gy": float(data["gy"]),
            "gz": float(data["gz"]),
            "timestamp": timestamp
        }

        latest_sensor_data = current
        sensor_data_history.append(current)

        print(f"[SENSOR] T:{current['temperature']:.2f}°C, "
              f"A({current['ax']:.2f},{current['ay']:.2f},{current['az']:.2f})g, "
              f"GZ:{current['gz']:.2f}dps", flush=True)

        return jsonify({"status": "success", "timestamp": timestamp}), 200

    except ValueError as ve:
        raw = request.get_data(as_text=True)
        print(f"[TYPE ERROR] Float conversion failed: {ve}\nRaw: {raw}", flush=True)
        traceback.print_exc()
        return jsonify({"error": "Invalid numeric format in sensor data"}), 400

    except Exception as e:
        raw = request.get_data(as_text=True)
        print(f"[GENERAL ERROR] {e}\nRaw: {raw}", flush=True)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():

    if latest_sensor_data["temperature"] is None:
        return jsonify({"message": "No data yet", "data": None}), 200
    return jsonify(latest_sensor_data), 200


@app.route('/sensor_data/history', methods=['GET'])
def get_sensor_data_history():
    return jsonify(list(sensor_data_history)), 200

head_position_data = {
    "position": "Center",
    "angle": 0.0,
    "timestamp": int(time.time())
}


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
perclos_data = {
    "status": "No Face", 
    "perclos": 0.0, 
    "ear": 0.0, 
    "yawn_status": "Closed", 
    "mar": 0.0, 
    "timestamp": int(time.time())
}
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
