# Daily Tracker - Silent Windows Activity Monitor

A robust, silent background tracker for Windows that monitors your system activity and generates detailed documentation every 15 minutes.

## Features

- **📸 Silent Screenshots** - Captures screenshots every 60 seconds (configurable) without any visible window
- **🖥️ Application Tracking** - Tracks which apps/windows you use and for how long
- **⌨️ Keystroke Logging** - Records all keyboard input with timestamps (with sensitive data redaction)
- **🖱️ Mouse Activity** - Tracks mouse moves, clicks, and scrolls
- **⚙️ Process Monitoring** - Snapshots running processes with command lines, CPU, and memory usage
- **🌐 Network/API Tracking** - Monitors active network connections and API endpoints
- **📄 Detailed Reports** - Generates comprehensive Markdown reports every 15 minutes
- **🔒 Privacy Protection** - Automatically redacts passwords, tokens, and API keys
- **🤫 Fully Silent** - Runs with no console window, no tray icon, no notifications
- **📊 Web Dashboard** - Full management and control panel with live monitoring

## Installation

### Quick Install (Recommended)

1. **Double-click** `install_startup.bat`
2. The installer will:
   - Install all Python dependencies
   - Create a startup shortcut (auto-starts at login)
   - Create data directories
   - Start the tracker silently

### Manual Install

```bash
cd daily-tracker
pip install -r requirements.txt
python run_tracker.py
```

## Usage

| Action | Command |
|--------|---------|
| **Start tracker** | Double-click `start_tracker.bat` |
| **Stop tracker** | Double-click `stop_tracker.bat` |
| **Install at startup** | Double-click `install_startup.bat` |
| **Run in foreground** | `python run_tracker.py` |
| **Open Dashboard** | Double-click `start_dashboard.bat` |
| **Dashboard URL** | http://127.0.0.1:5000 |
| **Open Desktop App** | Double-click `start_desktop_app.bat` |

## 🖥️ Desktop App

A native Windows desktop application with full management and control:

- **📈 Dashboard** - Real-time stats, activity feed, status indicator
- **📄 Reports** - Browse and view all reports
- **📸 Screenshots** - View screenshots with thumbnails
- **📁 Raw Data** - View complete JSON data
- **⚙️ Processes** - Live process monitoring
- **🌐 Network** - Live network connections
- **📋 Logs** - Real-time log viewer
- **⚡ Control Center** - Start/stop/restart tracker, generate reports, run cleanup, configure all settings

### Desktop App Features

- **Native Windows UI** - Built with CustomTkinter
- **Dark Theme** - Modern dark interface
- **Auto-Refresh** - Updates every 30 seconds
- **Full Configuration** - All settings configurable from the app
- **Message Dialogs** - Success/error notifications

## 📊 Web Dashboard

The dashboard provides full management and control:

- **📈 Overview** - Real-time stats, charts, recent activity
- **📄 Reports** - View all generated reports with markdown rendering
- **📸 Screenshots** - Browse and view all captured screenshots
- **📁 Raw Data** - View complete JSON tracking data
- **⚙️ Processes** - Live process monitoring with CPU/memory
- **🌐 Network** - Live network connection monitoring
- **📋 Logs** - Real-time tracker logs
- **⚡ Control Center** - Start/stop/restart tracker, generate reports, run cleanup, configure all settings

### Dashboard Features

- **Live Updates** - Server-Sent Events for real-time status
- **Full Configuration** - Change intervals, enable/disable tracking modules
- **Search & Filter** - Search reports and screenshots
- **Dark Theme** - Modern dark UI
- **Responsive** - Works on desktop and mobile

## Where Are My Reports?

All data is stored in the `data/` directory:

```
daily-tracker/
├── data/
│   ├── docs/          # 📄 Markdown reports (every 15 min)
│   ├── screenshots/   # 📸 Screenshot images
│   ├── logs/          # 📋 Tracker logs
│   └── raw/           # 📁 Raw JSON data
```

### Report Contents (Every 15 Minutes)

Each report includes:
1. **Interval Summary** - Overview of all activity
2. **Applications & Windows Used** - Which apps, for how long, percentage of interval
3. **Keystroke Activity** - Total keys, most frequent keys, typing sessions
4. **Mouse Activity** - Moves, clicks, scrolls with coordinates
5. **Running Processes** - All processes with command lines, CPU, memory
6. **Network & API Activity** - Remote endpoints, connections
7. **Screenshots** - List of captured screenshots with timestamps

## Configuration

Edit `config.json` (created after first run) or `tracker/config.py`:

```json
{
  "INTERVAL_MINUTES": 15,           // Report interval
  "SCREENSHOT_ENABLED": true,       // Enable/disable screenshots
  "SCREENSHOT_INTERVAL_SECONDS": 60, // Screenshot frequency
  "KEYBOARD_ENABLED": true,         // Enable/disable keyboard tracking
  "MOUSE_ENABLED": true,            // Enable/disable mouse tracking
  "PROCESS_ENABLED": true,          // Enable/disable process monitoring
  "NETWORK_ENABLED": true,          // Enable/disable network monitoring
  "WINDOW_ENABLED": true,           // Enable/disable window tracking
  "RETENTION_DAYS": 30              // Days of data to keep
}
```

## Privacy & Security

- **Sensitive data redaction**: Passwords, tokens, API keys, and secrets are automatically redacted from logs
- **Local storage only**: All data stays on your machine
- **Full control**: Easily disable any tracking module via config

## Requirements

- **Windows 10/11**
- **Python 3.8+** (with `pip`)

## Troubleshooting

**Tracker not starting?**
- Check `data/logs/tracker.log` for errors
- Ensure Python is in PATH: `python --version`
- Run `python run_tracker.py` in a terminal to see errors

**No reports generated?**
- Wait for the first 15-minute interval to complete
- Check that the tracker process is running: `tasklist | findstr pythonw`

**Screenshots not working?**
- Ensure `mss` is installed: `pip install mss`
- Check screen resolution and permissions

## Disclaimer

This tool is for personal productivity tracking and monitoring your own system. Use responsibly and in accordance with local laws and regulations. Do not use to monitor others without their consent.