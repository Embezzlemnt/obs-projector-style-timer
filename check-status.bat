@echo off
echo OBS Projector Timer - Helper Status
echo ===================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-RestMethod 'http://127.0.0.1:8765/state' | ConvertTo-Json } catch { 'Helper is not running. Run setup-auto-pause.bat or start-helper-hidden.vbs.' }"
echo.
pause
