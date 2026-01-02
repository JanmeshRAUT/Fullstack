# ✅ Connecting Vercel to Local Backend (Step-by-Step)

You have successfully installed ngrok and added your token. Now, follow these exact steps to connect everything.

---

### Step 1: Start the Backend Server

This runs your Python logic (ML + Arduino).

1.  Open **Terminal 1** in VS Code.
2.  Run:
    ```powershell
    cd backend
    python server.py
    ```
    _(Confirm it says "Running on http://0.0.0.0:5000")_

### Step 2: Start the Tunnel (ngrok)

This makes your localhost accessible from the internet.

1.  Open **Terminal 2** (Split Terminal or New Window).
2.  Run:
    ```powershell
    ngrok http 5000
    ```
3.  **COPY** the Forwarding URL it gives you.
    - Example: `https://a1b2-c3d4.ngrok-free.app`
    - _(Note: Copy the HTTPS one, not http)_

### Step 3: Configure Vercel

Tell your cloud frontend where to find your laptop.

1.  Go to your **Vercel Dashboard**.
2.  Select your **Fatigue Dashboard** project.
3.  Click **Settings** (top menu) -> **Environment Variables** (left menu).
4.  Find `REACT_APP_API_URL`.
    - If it exists: **Edit** it.
    - If not: **Add New**.
5.  Paste your ngrok URL as the value:
    - **Key:** `REACT_APP_API_URL`
    - **Value:** `https://your-copied-url.ngrok-free.app` (No trailing slash)
6.  Click **Save**.

### Step 4: Redeploy Frontend

Vercel needs to rebuild to bake in the new URL.

1.  Go to the **Deployments** tab in Vercel.
2.  Click the **three dots (...)** next to the latest deployment.
3.  Click **Redeploy**.
4.  Wait for it to finish (approx 1 min).

### Step 5: Test It

1.  Open the **Vercel App URL** on your phone or laptop.
2.  It should now show live data from your camera/sensors!
