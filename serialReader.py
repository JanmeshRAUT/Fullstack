from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route("/sensor", methods=["POST"])
def receive_sensor_data():
    data = request.json
    data["timestamp"] = datetime.now().isoformat()

    print("📥 Data received:", data)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
