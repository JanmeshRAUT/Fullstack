# 🚀 FatigueGuard Pro - Desktop Server Control

## Quick Setup (3 Steps)

### **Step 1: Locate Your Fullstack Folder**
Find where your Fullstack project is located:
- **E drive:** `E:\Fullstack`
- **Desktop:** `C:\Users\YourName\Desktop\Fullstack`
- **Documents:** `C:\Users\YourName\Documents\Fullstack`

### **Step 2: Copy Batch File to Desktop**

**Option A: Auto-Detect (Recommended)**
1. Copy `START_SERVER.bat` to your Desktop
2. Double-click it
3. It will auto-find your Fullstack folder
4. Done! ✅

**Option B: Manual Path**
1. Edit `START_SERVER_SIMPLE.bat` 
2. Change this line to your path:
   ```batch
   set "FULLSTACK_FOLDER=E:\Fullstack"
   ```
3. Copy to Desktop
4. Double-click to start
5. Done! ✅

**Option C: Create Shortcut**
1. Run `CreateDesktopShortcut.bat`
2. It creates a shortcut on your Desktop
3. Double-click the shortcut anytime
4. Done! ✅

### **Step 3: Start Server**

1. **Double-click** `START_SERVER.bat` (or shortcut)
2. **Wait** for it to start (takes 10-15 seconds)
3. **Look for** this output:
   ```
   🚀 Public backend URL: https://abc123def456.ngrok.io
   ```
4. **Copy** the URL

---

## Update Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. **Settings** → **Environment Variables**
4. Find `REACT_APP_API_URL`
5. **Paste** the ngrok URL you copied
6. Click **Save**
7. Push to GitHub to redeploy

---

## ⚠️ Important Notes

- **Keep the batch window OPEN** while using Vercel
- **New URL each restart** - update Vercel env var every time
- **Keep terminal running** for 2+ hours (free ngrok limit)
- **Check connection** - Vercel will connect automatically

---

## File Guide

| File | Purpose |
|------|---------|
| `START_SERVER.bat` | Smart auto-detect version (recommended) |
| `START_SERVER_SIMPLE.bat` | Simple version (manual path) |
| `CreateDesktopShortcut.bat` | Creates desktop shortcut |
| `VERCEL_SETUP.md` | Full Vercel configuration guide |

---

## Troubleshooting

### "Python not found"
- Install Python: https://www.python.org/
- Check "Add Python to PATH"
- Restart computer

### "Cannot find Fullstack folder"
- Edit `START_SERVER_SIMPLE.bat`
- Enter correct path (no quotes needed)

### "ngrok not working"
- Run: `pip install pyngrok`
- Or batch will install it automatically

### "Port 5000 already in use"
- Another app is using port 5000
- Restart your computer
- Or change port in `config.py`

---

## Success Indicators

✅ Server started when you see:
```
🚀 Public backend URL: https://abc123def456.ngrok.io
```

✅ Vercel connected when Vercel frontend loads data:
- Heart rate updates
- Head position tracking
- Fatigue status

✅ Check browser console for errors if data doesn't load

---

## Quick Commands (If Needed)

Open terminal in backend folder and run:

```bash
# Start with ngrok
python run_with_ngrok.py

# Start without ngrok (local only)
python server.py

# Check if Python works
python --version

# Install dependencies
pip install -r requirements.txt
```

---

**Need Help?** Check the terminal window for error messages!
