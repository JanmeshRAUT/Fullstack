from flask import Flask
from flask_cors import CORS
import threading
from sensors.serial_reader import start_serial_thread
from routes.api_routes import api_bp

print("[DIAGNOSTIC] Environment OK ✅")

app = Flask(__name__)
CORS(app)

# Register Blueprints
app.register_blueprint(api_bp)

if __name__ == '__main__':
    start_serial_thread()
    app.run(host='0.0.0.0', port=5000, debug=False)
