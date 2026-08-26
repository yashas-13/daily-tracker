@echo off
REM ============================================
REM Daily Tracker - Dashboard Launcher
REM Starts the web dashboard
REM ============================================
setlocal

echo.
echo ============================================
echo   Daily Tracker - Dashboard
echo ============================================
echo.

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo Starting Dashboard...
echo Dashboard will open at http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the dashboard.
echo.

cd /d "%SCRIPT_DIR%"
python run_dashboard.py

pause