$WshShell = New-Object -comObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\Start Fatigue System.lnk")
$Shortcut.TargetPath = "e:\Fullstack\START_SYSTEM.bat"
$Shortcut.WindowStyle = 1
$Shortcut.IconLocation = "shell32.dll,238"
$Shortcut.Description = "One-Click Start for Fatigue Guard"
$Shortcut.WorkingDirectory = "e:\Fullstack"
$Shortcut.Save()
Write-Host "Shortcut created on Desktop: 'Start Fatigue System'"
