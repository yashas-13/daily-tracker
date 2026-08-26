@echo off
REM ============================================
REM Daily Tracker - Stop Script
REM Stops the running tracker process
REM ============================================
setlocal

echo.
echo ============================================
echo   Daily Tracker - Stop
echo ============================================
echo.

echo Stopping Daily Tracker process...
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq *DailyTracker*" >nul 2>nul

REM Also kill any pythonw running run_tracker.py
for /f "tokens=2" %%p in ('wmic process where "name='pythonw.exe' and commandline like '%%run_tracker.py%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    echo Killing PID %%p...
    taskkill /f /pid %%p >nul 2>nul
)

echo.
echo Daily Tracker stopped.
echo.
echo To restart, run: start_tracker.bat
echo.
pause