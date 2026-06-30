@echo off
echo OBS Projector Timer - Helper Status
echo ===================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $s = Invoke-RestMethod 'http://127.0.0.1:8765/state'; $s | ConvertTo-Json; if ($s.camera_ok) { ''; 'Auto-pause is connected.' } else { ''; 'The helper is running and waiting for a camera feed.'; 'If OBS uses the webcam, click Start Virtual Camera in OBS.' } } catch { 'Helper is not running. Run INSTALL - OBS Projector Timer.bat.' }"
echo.
pause
