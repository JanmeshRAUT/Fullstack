# run_with_ngrok.py
from pyngrok import ngrok
import os
import threading
from server import app
import time

# ✏️ Change this path to your frontend folder
FRONTEND_ENV_PATH = r"E:\Fullstack\frontend\.env"

def update_frontend_env(public_url):
    try:
        env_line = f"REACT_APP_API_URL={public_url}\n"

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
                lines.append(env_line)

            with open(FRONTEND_ENV_PATH, "w") as f:
                f.writelines(lines)
        else:
            with open(FRONTEND_ENV_PATH, "w") as f:
                f.write(env_line)

        print(f"✅ Updated {FRONTEND_ENV_PATH} with:\n   {env_line.strip()}")
    except Exception as e:
        print(f"⚠️ Could not update frontend .env file: {e}")

def start_ngrok():
    port = 5000
    public_url = ngrok.connect(port).public_url
    print(f"\n🚀 Public backend URL: {public_url}\n")
    print("👉 Use this URL in your Vercel frontend or local React app:")
    print(f"   const API_URL = '{public_url}'\n")

    update_frontend_env(public_url)
    os.environ["BASE_URL"] = public_url

def run_app():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=start_ngrok, daemon=True).start()
    time.sleep(2)
    run_app()
