import requests
import json

URL = "https://fatigue-backend-40t1.onrender.com"

print(f"🔍 Testing Backend: {URL}")

# 1. Test Home Route
try:
    r = requests.get(f"{URL}/")
    print(f"✅ Home Check: {r.status_code} - {r.text}")
except Exception as e:
    print(f"❌ Home Check Failed: {e}")

# 2. Test Sensor Data Route
try:
    r = requests.get(f"{URL}/sensor_data")
    print(f"✅ Sensor Data: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"❌ Sensor Data Failed: {e}")
