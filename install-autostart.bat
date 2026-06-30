@echo off
set "SOURCE=%~dp0start-helper-hidden.vbs"
set "TARGET=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\OBS Projector Timer Helper.vbs"
copy /Y "%SOURCE%" "%TARGET%" >nul
echo Installed. The helper starts quietly with Windows and finds the camera automatically.
powershell -NoProfile -Command "Start-Sleep -Seconds 3" >nul
