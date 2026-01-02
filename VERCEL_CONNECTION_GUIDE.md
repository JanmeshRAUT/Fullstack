# Connecting Vercel Frontend to Local Backend

Since your backend runs locally (for Arduino/Camera access) but your frontend is on Vercel (Cloud), you need a **Tunnel**.

Here are the 3 best ways to bridge them:

## 🏆 Option 1: ngrok (Recommended)

**Best for:** Stability, Security, and Debugging.

1.  **Install:** [Download ngrok](https://ngrok.com/download).
2.  **Auth (Once):** `ngrok config add-authtoken <YOUR_TOKEN>`
3.  **Run:**
    ```powershell
    ngrok http 5000
    ```
4.  **Result:** Use the `https://xxxx.ngrok-free.app` URL.

## 🚀 Option 2: Localtunnel (Easiest / Free)

**Best for:** Quick testing if you have Node.js installed. No account needed.

1.  **Install:**
    ```powershell
    npm install -g localtunnel
    ```
2.  **Run:**
    ```powershell
    lt --port 5000
    ```
3.  **Result:** It gives a URL like `https://tender-wombat-45.loca.lt`.
    > **Note:** Localtunnel sometimes shows a warning page on first visit. You might need to visit the URL once in your browser to "click to continue" before the API works.

## ☁️ Option 3: Cloudflare Tunnel (Best for Static URLs)

**Best for:** Long-term use without changing URLs every time.

1.  Install `cloudflared`.
2.  Run: `cloudflared tunnel --url http://localhost:5000`

---

## 🔗 Final Step: Connect Vercel to Tunnel

Whichever option you choose, take the **HTTPS URL** it generates and:

1.  Go to **Vercel Dashboard** > Select Project > **Settings** > **Environment Variables**.
2.  Add/Edit Variable:
    - **Key:** `REACT_APP_API_URL`
    - **Value:** `https://your-generated-url.app` (No trailing slash)
3.  **Redeploy** (Deployments > Redeploy) or trigger a new build.

### ⚡ Operational Workflow

To run your system:

1.  **Laptop:** Run `python server.py`
2.  **Laptop:** Run `ngrok http 5000` (or `lt --port 5000`)
3.  **Laptop:** Update Vercel Env Var if the URL changed (Free ngrok/lt changes URL on restart).
4.  **Browser:** Open your Vercel App.
