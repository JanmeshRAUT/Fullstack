@echo off
TITLE Sensor Bridge (Fatigue Detection)
COLOR 0A
echo ===================================================
echo   FATIGUE DETECTION SYSTEM - SENSOR BRIDGE
echo ===================================================
echo.
echo [INFO] Connecting Local Utils (COM6) to Render Cloud...
echo.

:: Navigate to project folder
e:
cd e:\Fullstack

:: Run the bridge script
python backend/bridge.py

:: If it crashes, keep window open so user can see why
echo.
echo [ERROR] Bridge crashed or stopped.
pause
