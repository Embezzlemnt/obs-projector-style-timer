@echo off
set "TARGET=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\OBS Projector Timer Helper.vbs"
if exist "%TARGET%" del "%TARGET%"
echo Removed OBS Projector Timer helper from Windows startup.
powershell -NoProfile -Command "Start-Sleep -Seconds 3" >nul
