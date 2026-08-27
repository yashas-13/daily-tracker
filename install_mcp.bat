@echo off
REM ============================================
REM  Install Daily Tracker MCP Server
REM  Copies config to Claude Desktop / Cursor
REM ============================================
echo.
echo =============================================
echo   Daily Tracker - MCP Server Installer
echo =============================================
echo.

set TRACKER_DIR=%~dp0
set MCP_EXE=%TRACKER_DIR%run_mcp.py

REM --- Claude Desktop (Windows) ---
set CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json
echo [1] Installing for Claude Desktop...
if exist "%CLAUDE_CONFIG%" (
    echo     Config exists at: %CLAUDE_CONFIG%
    echo     Copy to merge manually or overwrite.
    echo     Config file: %TRACKER_DIR%mcp_configs\claude_desktop.json
) else (
    mkdir "%APPDATA%\Claude" 2>nul
    echo     Creating config at: %CLAUDE_CONFIG%
)

REM --- Cursor ---
set CURSOR_CONFIG=%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
echo [2] Installing for Cursor...
if not exist "%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings" (
    mkdir "%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings" 2>nul
)

echo.
echo =============================================
echo   Manual Config Steps:
echo =============================================
echo.
echo   Copy the contents of the appropriate config
echo   file to your tool's MCP settings:
echo.
echo   Claude Desktop:
echo     %CLAUDE_CONFIG%
echo     Source: %TRACKER_DIR%mcp_configs\claude_desktop.json
echo.
echo   Cursor:
echo     Settings > MCP Servers > Add
echo     Command: python "%MCP_EXE%"
echo.
echo   Windsurf / VS Code:
echo     Settings > MCP > Add Server
echo     Command: python "%MCP_EXE%"
echo.
echo   Claude Code (CLI):
echo     claude mcp add daily-tracker python "%MCP_EXE%"
echo.
echo   SSE mode (any HTTP client):
echo     python "%MCP_EXE%" --transport sse --port 8080
echo     Then point your client to: http://127.0.0.1:8080/sse
echo.
echo =============================================
echo   Done!
echo =============================================
pause