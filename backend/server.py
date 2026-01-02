from flask import Flask
from flask_cors import CORS
import threading
from sensors.serial_reader import start_serial_thread
from routes.api_routes import api_bp

print("[DIAGNOSTIC] Environment OK ✅")

app = Flask(__name__)
# Enable CORS for ALL domains and ALL headers to prevent blocking
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Register Blueprints
app.register_blueprint(api_bp)

import requests
import time

def print_ngrok_url():
    """Queries local ngrok API to find and print the public URL."""
    try:
        # Give ngrok a moment to start if run simultaneously
        time.sleep(2) 
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    print(f"\n[NGROK] 🌍 REQUIRED FRONTEND URL: {t['public_url']}\n")
                    return
    except Exception:
        pass # Ngrok not running or not accessible

if __name__ == '__main__':
    start_serial_thread()
    
    # Start a background thread to print URL so it doesn't block server start
    threading.Thread(target=print_ngrok_url, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
