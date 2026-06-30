@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "$me = $PID; Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $me -and ($_.CommandLine -like '*auto_pause_helper.py*' -or $_.CommandLine -like '*OBS auto pause helper.py*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo OBS Projector Timer helper stopped.
timeout /t 2 >nul
