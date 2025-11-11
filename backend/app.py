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

app = Flask(__name__)
CORS(app)
sensor_lock = threading.Lock()

# ========== GLOBAL STATES ==========
latest_sensor_data = {"temperature": None, "ax": None, "ay": None, "az": None,
                      "gx": None, "gy": None, "gz": None, "hr": None, "spo2": None,
                      "timestamp": None}

head_position_data = {"position": "Center", "angle_x": 0.0, "angle_y": 0.0,
                      "timestamp": int(time.time())}

perclos_data = {"status": "No Face", "perclos": 0.0, "ear": 0.0,
                "yawn_status": "Closed", "mar": 0.0, "adaptive_mar_thresh": 0.6,
                "timestamp": int(time.time())}


# ========== SERIAL SENSOR HANDLING ==========
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
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Arduino" in p.description or "CH340" in p.description or "ttyACM" in p.device:
            return p.device
    if ports:
        return ports[0].device
    raise Exception("No serial ports found. Connect Arduino via USB.")


def serial_reader():
    global latest_sensor_data
    try:
        port = find_arduino_port()
        ser = serial.Serial(port=port, baudrate=115200, timeout=1)
        print(f"[SERIAL] Listening on {port} at 115200 baud...")
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            parsed = parse_raw_sensor_string(line)
            if not parsed:
                continue
            timestamp = int(time.time())
            with sensor_lock:
                latest_sensor_data.update({**parsed, "timestamp": timestamp})
    except Exception as e:
        print(f"[SERIAL ERROR] {e}")
        traceback.print_exc()


# ========== HEAD POSITION ==========
def calculate_head_position(ax, ay, az):
    try:
        angle_x = math.degrees(math.atan2(ax, math.sqrt(ay**2 + az**2)))
        angle_y = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))

        vertical = "Up" if angle_x > 10 else "Down" if angle_x < -10 else "Center"
        horizontal = "Right" if angle_y > 10 else "Left" if angle_y < -10 else "Center"

        if vertical == "Center" and horizontal == "Center":
            position = "Center"
        elif vertical != "Center" and horizontal == "Center":
            position = vertical
        elif horizontal != "Center" and vertical == "Center":
            position = horizontal
        else:
            position = f"{vertical}-{horizontal}"

        return position, angle_x, angle_y
    except Exception:
        return "Unknown", 0.0, 0.0


# ========== FACE PROCESSING ==========
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


@app.route("/process_frame", methods=["POST"])
def process_frame():
    global perclos_data, eye_status_history, yawn_frames_count, mar_history
    now = int(time.time())
    try:
        data = request.get_json()
        if not data or "image_data" not in data:
            return jsonify({"error": "Missing image_data"}), 400

        base64_string = data["image_data"].split(",")[1]
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(base64_string), np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid frame data")

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        h, w, _ = frame.shape

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0]
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


@app.route("/combined_data", methods=["GET"])
def get_combined_data():
    hp = {"position": "Unknown", "angle_x": 0.0, "angle_y": 0.0, "timestamp": int(time.time())}

    if latest_sensor_data.get("ax") is not None:
        pos, ang_x, ang_y = calculate_head_position(
            latest_sensor_data["ax"],
            latest_sensor_data["ay"],
            latest_sensor_data["az"]
        )
        hp = {"position": pos, "angle_x": round(ang_x, 2), "angle_y": round(ang_y, 2), "timestamp": int(time.time())}

    return jsonify({
        "sensor": latest_sensor_data,
        "perclos": perclos_data,
        "head_position": hp,
        "server_time": int(time.time())
    }), 200


# ========== RUN SERVER ==========
if __name__ == "__main__":
    threading.Thread(target=serial_reader, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
