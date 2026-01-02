@echo off
TITLE Fatigue Guard Pro
e:\Fullstack\.venv\Scripts\python.exe -c "import ctypes; ctypes.windll.kernel32.SetConsoleTitleW('Fatigue Guard Pro')"

echo [1/2] Starting Ngrok Tunnel (Hidden)...
:: Start Ngrok Minimized
start /min "Ngrok Tunnel" cmd /c "ngrok http 5000 > nul"

:: Wait for Ngrok to initialize
timeout /t 3 /nobreak > nul

echo [2/2] Starting Backend Server...
echo.
echo ========================================================
echo   FATIGUE GUARD SYSTEM V1.0
echo ========================================================
echo.
echo   * Ngrok Tunnel: Running in background
echo   * Server: Starting...
echo.

:: Run Python in THIS window
cd backend
python server.py

pause
