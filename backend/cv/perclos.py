import cv2
import mediapipe as mp
import math
import time
import numpy as np
from collections import deque
import threading
from cv.head_pose import calculate_cv_head_pose, cv_head_angles, cv_angles_lock

# --- Constants & Configuration ---
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
EYE_AR_THRESH = 0.25
MOUTH_INNER = [13, 14, 78, 308]
MAR_THRESH = 0.6
MAR_FRAME_COUNT = 3

# --- State ---
perclos_data = {
    "status": "No Face",
    "perclos": 0.0,
    "ear": 0.0,
    "yawn_status": "Closed",
    "mar": 0.0,
    "adaptive_mar_thresh": 0.6,
    "timestamp": int(time.time())
}

eye_status_history = deque(maxlen=6)
yawn_frames_count = 0
mar_history = deque(maxlen=20)

# --- MediaPipe Initialization ---
mp_face_mesh = mp.solutions.face_mesh
# Initialize locally, or can be initialized on import
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1, 
    refine_landmarks=True, 
    min_detection_confidence=0.5
)

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

def process_face_mesh(frame):
    """
    Processes a frame using MediaPipe FaceMesh to update PERCLOS, Yawn, and Head Pose.
    Updates global state: perclos_data, cv_head_angles.
    """
    global perclos_data, eye_status_history, yawn_frames_count, mar_history
    now = int(time.time())

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        lm = results.multi_face_landmarks[0]
        
        # --- CV HEAD POSE FALLBACK ---
        try:
            cv_pitch, cv_yaw, cv_roll, is_calibrated = calculate_cv_head_pose(lm.landmark, w, h)
            with cv_angles_lock:
                cv_head_angles["pitch"] = cv_pitch
                cv_head_angles["yaw"] = cv_yaw
                cv_head_angles["roll"] = cv_roll
                cv_head_angles["is_calibrated"] = is_calibrated
        except Exception as cv_e:
            print(f"[CV POSE ERROR] {cv_e}")

        # --- PERCLOS / EAR ---
        left = [(lm.landmark[i].x * w, lm.landmark[i].y * h) for i in LEFT_EYE]
        right = [(lm.landmark[i].x * w, lm.landmark[i].y * h) for i in RIGHT_EYE]
        ear = (eye_aspect_ratio(left) + eye_aspect_ratio(right)) / 2
        eyes_closed = 1 if ear < EYE_AR_THRESH else 0
        eye_status_history.append(eyes_closed)
        perclos_val = (sum(eye_status_history) / len(eye_status_history)) * 100

        # --- YAWN / MAR ---
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
        # No face detected
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

    return perclos_data
