import os

class Config:
    """
    Central Configuration for the Backend Application
    """
    
    # --- Serial / Sensor Configuration ---
    # Defaulting to COM6 as per recent user diagnostics, but serial_reader will also auto-detect.
    ARDUINO_PORT = os.environ.get("ARDUINO_PORT", "COM6") 
    BAUD_RATE = int(os.environ.get("BAUD_RATE", 115200))
    MAX_HISTORY = 100 # Number of sensor readings to keep in memory
    SENSOR_TIMEOUT = 2.0 # Seconds before sensor data is considered "Stale"
    USE_MOCK_DATA = False # Set to True to enable random data generation when sensors are disconnected
    
    # --- ML Engine Configuration ---
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "fatigue_model.pkl")
    ML_INTERVAL = 0.5 # Seconds between ML predictions to prevent CPU overload
    
    # --- Logging / Debug ---
    DEBUG = True

def get_config():
    return Config()
