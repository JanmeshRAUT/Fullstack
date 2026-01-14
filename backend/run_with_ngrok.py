# run_with_ngrok.py
import uvicorn
from pyngrok import ngrok
import os
import threading
import time
import sys

# ✏️ Change this path to your frontend folder
FRONTEND_ENV_PATH = r"E:\Fullstack\frontend\.env"

def update_frontend_env(public_url):
    try:
        # Format for React .env
        env_line = f"REACT_APP_API_URL={public_url}\n"

        lines = []
        if os.path.exists(FRONTEND_ENV_PATH):
            with open(FRONTEND_ENV_PATH, "r") as f:
                lines = f.readlines()

        # Replace existing REACT_APP_API_URL or add if missing
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("REACT_APP_API_URL="):
                lines[i] = env_line
                updated = True
                break

        if not updated:
            if lines and not lines[-1].endswith('\n'):
                lines[-1] += '\n'
            lines.append(env_line)

        with open(FRONTEND_ENV_PATH, "w") as f:
            f.writelines(lines)

        print(f"✅ Updated {FRONTEND_ENV_PATH} with:\n   {env_line.strip()}")
    except Exception as e:
        print(f"⚠️ Could not update frontend .env file: {e}")

def start_ngrok():
    # Giving server a second to ensure port 5000 is claimed or ready? 
    # Actually ngrok can start whenever.
    time.sleep(1)
    try:
        # Check if auth token is needed for your specific static domain
        # If you have a static domain, you might need to configure it here:
        # url = ngrok.connect(5000, domain="nulliporous-carbolic-lianne.ngrok-free.dev").public_url
        
        # For now, we connect a generic tunnel. 
        # If you want the static one, user must configure pyngrok with their token.
        
        tunnel = ngrok.connect(5000)
        public_url = tunnel.public_url
        
        # Fix: Ensure HTTPS for frontend mixed content
        if public_url.startswith("http://"):
            public_url = public_url.replace("http://", "https://")
            
        print(f"\n==========================================================================================")
        print(f" 🚀 [NGROK] Public URL: {public_url}")
        print(f"==========================================================================================\n")

        update_frontend_env(public_url)
        
        # Keep thread alive to keep tunnel open
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
        
    except Exception as e:
        print(f"❌ Ngrok Error: {e}")

if __name__ == "__main__":
    # Start Ngrok in background thread
    threading.Thread(target=start_ngrok, daemon=True).start()
    
    # Start FastAPI with Uvicorn
    # Note: reload=False to avoid re-running ngrok logic on reload, 
    # or separate them. For production/demo, reload=False is safer.
    print(f"🔌 Starting FastAPI Server on Port 5000...")
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
