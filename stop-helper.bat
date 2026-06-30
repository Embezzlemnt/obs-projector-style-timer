@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*auto_pause_helper.py*' -or $_.CommandLine -like '*OBS auto pause helper.py*' -or $_.CommandLine -like '*OBS Timer Helper*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo OBS Projector Timer helper stopped.
timeout /t 2 >nul
