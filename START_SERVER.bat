@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================
REM FatigueGuard Pro - Server Startup Script
REM ============================================
REM This script can be placed anywhere (Desktop, etc)

cls
echo.
echo =====================================
echo FatigueGuard Pro - Backend Server
echo =====================================
echo.

REM Try to find the Fullstack folder automatically
REM Look in common locations
set "FOUND_PATH="

if exist "E:\Fullstack\backend" (
    set "FOUND_PATH=E:\Fullstack"
    goto found_path
)

if exist "C:\Users\%username%\Desktop\Fullstack\backend" (
    set "FOUND_PATH=C:\Users\%username%\Desktop\Fullstack"
    goto found_path
)

if exist "%UserProfile%\Desktop\Fullstack\backend" (
    set "FOUND_PATH=%UserProfile%\Desktop\Fullstack"
    goto found_path
)

if exist "%cd%\Fullstack\backend" (
    set "FOUND_PATH=%cd%\Fullstack"
    goto found_path
)

REM If not found automatically, ask user
:ask_path
cls
echo =====================================
echo FatigueGuard Pro - Backend Server
echo =====================================
echo.
echo Cannot find Fullstack folder automatically.
echo.
echo Please enter the full path to your Fullstack folder:
echo (Example: E:\Fullstack or C:\Users\YourName\Desktop\Fullstack)
echo.

set /p FULLSTACK_PATH="Enter path: "

if not exist "!FULLSTACK_PATH!\backend" (
    echo.
    echo ❌ ERROR: Backend folder not found at !FULLSTACK_PATH!\backend
    echo.
    pause
    goto ask_path
)

set "FOUND_PATH=!FULLSTACK_PATH!"
goto found_path

:found_path
echo ✅ Found Fullstack folder at: !FOUND_PATH!
echo.

REM Navigate to backend folder
cd /d "!FOUND_PATH!\backend"

if not exist "run_with_ngrok.py" (
    echo.
    echo ❌ ERROR: run_with_ngrok.py not found!
    echo Current directory: %cd%
    echo.
    pause
    exit /b 1
)

echo Preparing server startup...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Install/upgrade required packages
echo Installing required packages...
echo.

pip install -q pyngrok flask flask-cors opencv-python-headless mediapipe numpy pandas scikit-learn joblib

if %errorlevel% neq 0 (
    echo.
    echo ⚠️  Warning: Some packages may not have installed properly
    echo But we'll try to continue...
    echo.
    timeout /t 2
)

echo.
echo =====================================
echo Starting Backend Server with ngrok
echo =====================================
echo.
echo 🚀 Starting server at localhost:5000
echo 🌐 Creating public tunnel with ngrok...
echo.
echo This window will stay open while the server is running.
echo.
echo 📋 IMPORTANT:
echo When you see the ngrok URL (https://...ngrok.io):
echo 1. Copy the entire URL
echo 2. Go to Vercel Dashboard
echo 3. Settings → Environment Variables
echo 4. Update REACT_APP_API_URL with the URL
echo 5. Push to GitHub to redeploy
echo.
echo ⚠️  Keep this window OPEN while using your Vercel frontend!
echo.
echo =====================================
echo.

REM Run the Flask app with ngrok
python run_with_ngrok.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: Server failed to start
    echo.
)

echo.
echo Press any key to close this window...
pause >nul

