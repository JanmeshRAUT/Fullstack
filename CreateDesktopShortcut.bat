@echo off
REM Create Desktop Shortcut for Server Control
setlocal enabledelayedexpansion

echo.
echo =====================================
echo Create Desktop Shortcut
echo =====================================
echo.

REM Get Desktop path
set "DESKTOP=%UserProfile%\Desktop"

REM Get current directory of this batch file
set "BATCH_PATH=%~dp0START_SERVER.bat"

if not exist "%BATCH_PATH%" (
    echo ERROR: Could not find START_SERVER.bat
    echo Make sure this script is in the same folder as START_SERVER.bat
    pause
    exit /b 1
)

REM Create shortcut using PowerShell
echo Creating shortcut...
echo.

powershell -NoProfile -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\FatigueGuard Pro - Start Server.lnk'); $Shortcut.TargetPath = '%BATCH_PATH%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'C:\Windows\System32\cmd.exe,0'; $Shortcut.Save(); Write-Host 'Shortcut created successfully!'"

if %errorlevel% equ 0 (
    echo.
    echo ✅ Shortcut created on Desktop!
    echo Name: "FatigueGuard Pro - Start Server.lnk"
    echo.
    echo You can now double-click it to start the server!
) else (
    echo.
    echo ⚠️  Could not create shortcut automatically
    echo You can manually:
    echo 1. Right-click START_SERVER.bat
    echo 2. Select "Create shortcut"
    echo 3. Move to Desktop
)

echo.
pause
