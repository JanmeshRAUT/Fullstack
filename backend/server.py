from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import uvicorn
from contextlib import asynccontextmanager

from sensors.serial_reader import start_serial_thread
from routes.api_routes import router as api_router

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[DIAGNOSTIC] Starting Serial Thread...")
    start_serial_thread()
    threading.Thread(target=print_ngrok_url, daemon=True).start()
    yield
    # Shutdown logic if needed

print("[DIAGNOSTIC] Environment OK ✅")

app = FastAPI(lifespan=lifespan)

# Enable CORS for ALL domains and ALL headers to prevent blocking
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Router
app.include_router(api_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)
