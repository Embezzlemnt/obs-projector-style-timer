@echo off
setlocal
cd /d "%~dp0"
echo.
echo OBS Projector Timer - Auto Pause Setup
echo ======================================
echo.
echo 1. If OBS already uses your webcam, click "Start Virtual Camera" in OBS first.
echo 2. This setup will scan camera indexes.
echo 3. It also saves preview images for available camera indexes.
echo 4. Pick the number whose preview image shows the camera feed you want.
echo.
pause
echo.
python "%~dp0auto_pause_helper.py" --scan --save-previews 2>nul
echo.
if exist "%~dp0camera-previews" start "" "%~dp0camera-previews"
echo.
set /p CAMERA_INDEX=Type the camera index to use, then press Enter: 
if "%CAMERA_INDEX%"=="" set CAMERA_INDEX=0
echo.
echo Saving camera index %CAMERA_INDEX%...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Join-Path '%~dp0' 'timer-helper-settings.json'; $j = Get-Content -LiteralPath $p -Raw | ConvertFrom-Json; $j.camera = [int]'%CAMERA_INDEX%'; $j | ConvertTo-Json | Set-Content -LiteralPath $p -Encoding UTF8"
echo.
echo Restarting hidden helper...
call "%~dp0stop-helper.bat" >nul 2>&1
wscript "%~dp0start-helper-hidden.vbs"
timeout /t 2 >nul
echo.
echo Current helper state:
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-RestMethod 'http://127.0.0.1:8765/state' | ConvertTo-Json } catch { 'Helper did not answer yet. Run start-helper-hidden.vbs and try again.' }"
echo.
echo If camera_ok is true, auto-pause is connected.
echo If camera_ok is false, run this setup again and choose another available index.
echo.
pause
