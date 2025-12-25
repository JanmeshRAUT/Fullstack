import serial
import serial.tools.list_ports
import threading
import time
import math
import traceback
from collections import deque

# --- Global State ---
sensor_lock = threading.Lock()

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

def calculate_head_position(ax, ay, az):
    try:
        # PITCH (Up/Down) - Rotation around X-axis
        # atan2(x, sqrt(y*y + z*z))
        angle_x = math.degrees(math.atan2(ax, math.sqrt(ay**2 + az**2)))
        
        # YAW (Left/Right) - Rotation around Y-axis
        # atan2(y, sqrt(x*x + z*z))
        angle_y = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
        
        # ROLL (Tilt Left/Right) - Rotation around Z-axis
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

def update_head_position_data():
    """Updates the global head_position_data based on latest sensor values."""
    ax = latest_sensor_data["ax"]
    ay = latest_sensor_data["ay"]
    az = latest_sensor_data["az"]

    if ax is None or ay is None or az is None:
        return head_position_data # Return existing or update to unknown?

    pos, ang_x, ang_y, ang_z = calculate_head_position(ax, ay, az)

    head_position_data.update({
        "position": pos,
        "angle_x": round(ang_x, 2),
        "angle_y": round(ang_y, 2),
        "angle_z": round(ang_z, 2),
        "timestamp": int(time.time())
    })
    return head_position_data

def serial_reader():
    global latest_sensor_data, sensor_data_history
    try:
        port = find_arduino_port()
        ser = serial.Serial(port=port, baudrate=115200, timeout=1)
        print(f"[SERIAL] ✅ Connected to {port}")
        
        while True:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                        
                    print(f"\n[ARDUINO RAW] >>> {line}") 
                    
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

def start_serial_thread():
    t = threading.Thread(target=serial_reader, daemon=True)
    t.start()
