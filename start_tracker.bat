@echo off
REM ============================================
REM Daily Tracker - Start Script
REM Starts the tracker silently
REM ============================================
setlocal

echo.
echo ============================================
echo   Daily Tracker - Start
echo ============================================
echo.

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Check if already running
tasklist /fi "imagename eq pythonw.exe" 2>nul | find /i "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo Daily Tracker may already be running.
    echo If not, stop it first with stop_tracker.bat, then try again.
    echo.
    pause
    exit /b 0
)

echo Starting Daily Tracker silently...
start "" wscript.exe "%SCRIPT_DIR%\run_silent.vbs"
echo.
echo Daily Tracker started. It will run in the background.
echo Reports are saved to: %SCRIPT_DIR%\data\docs\
echo.
pause