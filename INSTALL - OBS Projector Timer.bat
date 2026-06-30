@echo off
setlocal
cd /d "%~dp0"
title OBS Projector Timer Setup
echo.
echo OBS Projector Timer
echo ===================
echo.
echo Setting up the quiet background helper...
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3 from https://www.python.org/downloads/
  echo During install, check "Add Python to PATH", then run this file again.
  echo.
  pause
  exit /b 1
)

python -c "import cv2" >nul 2>nul
if errorlevel 1 (
  echo Installing the camera helper package. This can take a minute...
  python -m pip install --upgrade pip >nul 2>nul
  python -m pip install opencv-python >nul
  if errorlevel 1 (
    echo Setup could not install the camera package.
    echo Check your internet connection, then run this file again.
    echo.
    pause
    exit /b 1
  )
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Join-Path '%~dp0' 'timer-helper-settings.json'; if (Test-Path -LiteralPath $p) { $j = Get-Content -LiteralPath $p -Raw | ConvertFrom-Json } else { $j = [pscustomobject]@{} }; $j | Add-Member -NotePropertyName camera -NotePropertyValue 'auto' -Force; $j | Add-Member -NotePropertyName port -NotePropertyValue 8765 -Force; $j | Add-Member -NotePropertyName pause -NotePropertyValue 3.0 -Force; $j | Add-Member -NotePropertyName resume -NotePropertyValue 0.5 -Force; $j | Add-Member -NotePropertyName interval -NotePropertyValue 0.12 -Force; $j | Add-Member -NotePropertyName presence_threshold -NotePropertyValue 0.32 -Force; $j | ConvertTo-Json | Set-Content -LiteralPath $p -Encoding UTF8"

call "%~dp0stop-helper.bat" >nul 2>nul

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
copy /Y "%~dp0start-helper-hidden.vbs" "%STARTUP%\OBS Projector Timer Helper.vbs" >nul

wscript "%~dp0start-helper-hidden.vbs"
timeout /t 3 >nul

echo.
echo Setup is ready.
echo Add this local file in OBS Browser Source:
echo %~dp0obs-projector-timer.html
echo.
echo Auto-pause is automatic. If OBS already owns your webcam, start OBS Virtual Camera.
echo The helper will keep trying quietly until it sees a camera feed.
echo.
echo To stop it later, double-click stop-helper.bat.
echo.
pause
