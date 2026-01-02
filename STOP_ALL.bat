@echo off
TITLE Stop Fatigue System
echo ===================================================
echo   STOPPING FATIGUE SYSTEM...
echo ===================================================
echo.

:: 1. Force Kill Python Server
taskkill /IM python.exe /F
echo [OK] Python Server Stopped.

:: 2. Force Kill Ngrok
taskkill /IM ngrok.exe /F
echo [OK] Ngrok Tunnel Stopped.

echo.
echo ===================================================
echo   ALL SYSTEMS DOWN.
echo ===================================================
timeout /t 3 > nul
