@echo off
cd /d "%~dp0"
python "%~dp0auto_pause_helper.py" --scan --save-previews 2>nul
pause
