@echo off
set "SOURCE=%~dp0start-helper-hidden.vbs"
set "TARGET=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\OBS Projector Timer Helper.vbs"
copy /Y "%SOURCE%" "%TARGET%" >nul
echo Installed. The helper will start quietly when Windows starts.
timeout /t 3 >nul
