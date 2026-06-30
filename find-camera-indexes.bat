@echo off
cd /d "%~dp0"
setlocal
set "PYTHON_CMD="
where python >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD (
  echo Python was not found.
  pause
  exit /b 1
)
%PYTHON_CMD% "%~dp0auto_pause_helper.py" --scan --save-previews 2>nul
pause
