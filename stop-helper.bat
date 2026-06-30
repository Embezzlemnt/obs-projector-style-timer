@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "$me = $PID; Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $me -and $_.Name -match '^(python|pythonw|cmd|wscript|cscript)\.exe$' -and ($_.CommandLine -like '*auto_pause_helper.py*' -or $_.CommandLine -like '*OBS auto pause helper.py*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo OBS Projector Timer helper stopped.
powershell -NoProfile -Command "Start-Sleep -Seconds 2" >nul
