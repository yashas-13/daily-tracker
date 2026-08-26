@echo off
REM ============================================
REM Daily Tracker - Desktop App Launcher
REM Starts the native Windows desktop application
REM ============================================
setlocal

echo.
echo ============================================
echo   Daily Tracker - Desktop App
echo ============================================
echo.

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo Starting Desktop App...
echo.

cd /d "%SCRIPT_DIR%"
python desktop_app.py

pause