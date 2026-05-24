@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 run.py --wizard
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python run.py --wizard
  exit /b %errorlevel%
)

echo Python was not found. Install Python 3.10+ from https://www.python.org/downloads/
pause
exit /b 1
