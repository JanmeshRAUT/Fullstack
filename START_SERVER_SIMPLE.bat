@echo off
REM ============================================
REM FatigueGuard Pro - Simple Version
REM Run this from Desktop
REM ============================================

setlocal enabledelayedexpansion

cls
echo.
echo =====================================
echo FatigueGuard Pro - Server Control
echo =====================================
echo.

REM Edit this path to your Fullstack folder location
REM For Desktop: C:\Users\YourUsername\Desktop\Fullstack
REM For E drive: E:\Fullstack
set "FULLSTACK_FOLDER=E:\Fullstack"

REM Verify path exists
if not exist "!FULLSTACK_FOLDER!\backend" (
    echo.
    echo ERROR: Cannot find Fullstack folder at:
    echo !FULLSTACK_FOLDER!
    echo.
    echo SOLUTION: Edit this file and change FULLSTACK_FOLDER to your path
    echo.
    pause
    exit /b 1
)

REM Navigate to backend
cd /d "!FULLSTACK_FOLDER!\backend"

echo ✅ Starting server from: !cd!
echo.

REM Install packages quietly
echo Installing dependencies...
pip install -q pyngrok flask flask-cors >nul 2>&1

echo.
echo 🚀 Server starting...
echo.

REM Start the server
python run_with_ngrok.py

pause
