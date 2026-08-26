@echo off
REM ============================================
REM Daily Tracker - Startup Installer
REM Installs the tracker to run silently at login
REM ============================================
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   Daily Tracker - Startup Installation
echo ============================================
echo.

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/4] Installing Python dependencies...
cd /d "%SCRIPT_DIR%"
python -m pip install --upgrade pip >nul 2>nul
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo       Dependencies installed successfully.
echo.

echo [2/4] Creating startup shortcut...
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_PATH=%SCRIPT_DIR%\run_silent.vbs"

REM Create a shortcut in the Startup folder using PowerShell
powershell -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$s = $ws.CreateShortcut('%STARTUP_DIR%\DailyTracker.lnk');" ^
  "$s.TargetPath = 'wscript.exe';" ^
  "$s.Arguments = '\"%VBS_PATH%\"';" ^
  "$s.WorkingDirectory = '%SCRIPT_DIR%';" ^
  "$s.Description = 'Daily Tracker - Silent Activity Monitor';" ^
  "$s.Save()"

if %errorlevel% neq 0 (
    echo [ERROR] Failed to create startup shortcut.
    pause
    exit /b 1
)
echo       Startup shortcut created.
echo.

echo [3/4] Creating data directories...
if not exist "%SCRIPT_DIR%\data\screenshots" mkdir "%SCRIPT_DIR%\data\screenshots"
if not exist "%SCRIPT_DIR%\data\docs" mkdir "%SCRIPT_DIR%\data\docs"
if not exist "%SCRIPT_DIR%\data\logs" mkdir "%SCRIPT_DIR%\data\logs"
if not exist "%SCRIPT_DIR%\data\raw" mkdir "%SCRIPT_DIR%\data\raw"
echo       Data directories created.
echo.

echo [4/4] Starting the tracker now...
start "" wscript.exe "%VBS_PATH%"
echo       Tracker started silently.
echo.

echo ============================================
echo   Installation Complete!
echo.
echo   The Daily Tracker is now running silently.
echo   It will automatically start when you log in.
echo.
echo   Reports are saved to: %SCRIPT_DIR%\data\docs\
echo   Screenshots are saved to: %SCRIPT_DIR%\data\screenshots\
echo.
echo   To stop the tracker, run: stop_tracker.bat
echo ============================================
echo.
pause