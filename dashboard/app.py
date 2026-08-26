"""Daily Tracker Dashboard - Web-based management and control panel."""
import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, jsonify, request, send_from_directory, Response, redirect, url_for

from tracker import config
from tracker.logger import log

app = Flask(__name__)
app.config["SECRET_KEY"] = "daily-tracker-dashboard"

# Global tracker instance reference
tracker_instance = None

# Data directory
DATA_DIR = config.DATA_DIR


def get_tracker_status():
    """Get the current status of the tracker."""
    global tracker_instance
    if tracker_instance and tracker_instance._running:
        return {
            "running": True,
            "started_at": getattr(tracker_instance, "_started_at", None),
            "interval_minutes": config.INTERVAL_MINUTES,
        }
    return {"running": False, "started_at": None, "interval_minutes": config.INTERVAL_MINUTES}


def get_reports():
    """Get list of all generated reports."""
    reports = []
    docs_dir = config.DOCS_DIR
    if docs_dir.exists():
        for f in sorted(docs_dir.glob("report_*.md"), reverse=True):
            try:
                stats = f.stat()
                reports.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "date": f.name.replace("report_", "").replace(".md", "").split("_")[0],
                    "time": f.name.replace("report_", "").replace(".md", "").split("_")[1],
                })
            except Exception:
                continue
    return reports


def get_screenshots():
    """Get list of all screenshots."""
    screenshots = []
    shots_dir = config.SCREENSHOTS_DIR
    if shots_dir.exists():
        for f in sorted(shots_dir.glob("*.jpg"), reverse=True):
            try:
                stats = f.stat()
                screenshots.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "date": f.name[:8],
                    "time": f"{f.name[8:10]}:{f.name[10:12]}:{f.name[12:14]}",
                })
            except Exception:
                continue
    return screenshots


def get_raw_data():
    """Get list of all raw data files."""
    raw_files = []
    raw_dir = config.RAW_DIR
    if raw_dir.exists():
        for f in sorted(raw_dir.glob("raw_*.json"), reverse=True):
            try:
                stats = f.stat()
                raw_files.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                })
            except Exception:
                continue
    return raw_files


def get_logs():
    """Get recent log entries."""
    log_file = config.LOGS_DIR / "tracker.log"
    if not log_file.exists():
        return []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-200:]  # Last 200 lines
    except Exception:
        return []


def get_disk_usage():
    """Get disk usage of data directory."""
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(DATA_DIR):
        for f in files:
            try:
                total_size += os.path.getsize(os.path.join(root, f))
                file_count += 1
            except Exception:
                continue
    return {
        "total_size": total_size,
        "file_count": file_count,
        "size_mb": round(total_size / (1024 * 1024), 2),
    }


def get_activity_summary():
    """Get activity summary from recent reports."""
    reports = get_reports()
    if not reports:
        return {
            "total_reports": 0,
            "total_screenshots": 0,
            "last_report": None,
            "today_reports": 0,
        }
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_reports = [r for r in reports if r["date"] == today]
    
    return {
        "total_reports": len(reports),
        "total_screenshots": len(get_screenshots()),
        "last_report": reports[0]["modified"] if reports else None,
        "today_reports": len(today_reports),
    }


# ============ Routes ============

@app.route("/")
def index():
    """Dashboard home page."""
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    """Get tracker status."""
    return jsonify(get_tracker_status())


@app.route("/api/overview")
def api_overview():
    """Get overview data for dashboard."""
    activity = get_activity_summary()
    disk = get_disk_usage()
    status = get_tracker_status()
    
    # Get recent reports data for charts
    reports = get_reports()[:24]  # Last 24 reports
    report_dates = [r["date"] for r in reports]
    report_times = [r["time"] for r in reports]
    
    # Count reports per day
    from collections import Counter
    daily_counts = Counter(r["date"] for r in get_reports())
    last_7_days = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        last_7_days.append({
            "date": day,
            "count": daily_counts.get(day, 0),
        })
    
    return jsonify({
        "status": status,
        "activity": activity,
        "disk": disk,
        "daily_reports": last_7_days,
        "recent_reports": reports[:10],
        "recent_screenshots": get_screenshots()[:10],
    })


@app.route("/api/reports")
def api_reports():
    """Get all reports."""
    return jsonify(get_reports())


@app.route("/api/reports/<filename>")
def api_report(filename):
    """Get a specific report content."""
    filepath = config.DOCS_DIR / filename
    if not filepath.exists():
        return jsonify({"error": "Report not found"}), 404
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"name": filename, "content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/screenshots")
def api_screenshots():
    """Get all screenshots."""
    return jsonify(get_screenshots())


@app.route("/api/screenshots/<filename>")
def api_screenshot(filename):
    """Serve a screenshot image."""
    return send_from_directory(config.SCREENSHOTS_DIR, filename)


@app.route("/api/raw")
def api_raw():
    """Get all raw data files."""
    return jsonify(get_raw_data())


@app.route("/api/raw/<filename>")
def api_raw_data(filename):
    """Get a specific raw data file."""
    filepath = config.RAW_DIR / filename
    if not filepath.exists():
        return jsonify({"error": "File not found"}), 404
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/logs")
def api_logs():
    """Get recent logs."""
    return jsonify(get_logs())


@app.route("/api/config")
def api_get_config():
    """Get current configuration."""
    return jsonify({
        "INTERVAL_MINUTES": config.INTERVAL_MINUTES,
        "SCREENSHOT_ENABLED": config.SCREENSHOT_ENABLED,
        "SCREENSHOT_INTERVAL_SECONDS": config.SCREENSHOT_INTERVAL_SECONDS,
        "KEYBOARD_ENABLED": config.KEYBOARD_ENABLED,
        "MOUSE_ENABLED": config.MOUSE_ENABLED,
        "PROCESS_ENABLED": config.PROCESS_ENABLED,
        "NETWORK_ENABLED": config.NETWORK_ENABLED,
        "WINDOW_ENABLED": config.WINDOW_ENABLED,
        "RETENTION_DAYS": config.RETENTION_DAYS,
    })


@app.route("/api/config", methods=["POST"])
def api_update_config():
    """Update configuration."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    updates = {}
    for key in ["INTERVAL_MINUTES", "SCREENSHOT_INTERVAL_SECONDS", "RETENTION_DAYS"]:
        if key in data:
            try:
                updates[key] = int(data[key])
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid value for {key}"}), 400
    
    for key in ["SCREENSHOT_ENABLED", "KEYBOARD_ENABLED", "MOUSE_ENABLED", 
                "PROCESS_ENABLED", "NETWORK_ENABLED", "WINDOW_ENABLED"]:
        if key in data:
            updates[key] = bool(data[key])
    
    if updates:
        for key, value in updates.items():
            setattr(config, key, value)
        config.save_config()
        log.info(f"Configuration updated: {updates}")
        return jsonify({"success": True, "updates": updates})
    
    return jsonify({"error": "No valid updates provided"}), 400


@app.route("/api/tracker/start", methods=["POST"])
def api_start_tracker():
    """Start the tracker."""
    global tracker_instance
    from tracker.main import DailyTracker
    
    if tracker_instance and tracker_instance._running:
        return jsonify({"success": False, "error": "Tracker is already running"})
    
    tracker_instance = DailyTracker()
    tracker_instance._started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tracker_instance.start()
    return jsonify({"success": True, "message": "Tracker started"})


@app.route("/api/tracker/stop", methods=["POST"])
def api_stop_tracker():
    """Stop the tracker."""
    global tracker_instance
    if tracker_instance and tracker_instance._running:
        tracker_instance.stop()
        return jsonify({"success": True, "message": "Tracker stopped"})
    return jsonify({"success": False, "error": "Tracker is not running"})


@app.route("/api/tracker/restart", methods=["POST"])
def api_restart_tracker():
    """Restart the tracker."""
    global tracker_instance
    from tracker.main import DailyTracker
    
    if tracker_instance and tracker_instance._running:
        tracker_instance.stop()
    
    tracker_instance = DailyTracker()
    tracker_instance._started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tracker_instance.start()
    return jsonify({"success": True, "message": "Tracker restarted"})


@app.route("/api/tracker/generate-report", methods=["POST"])
def api_generate_report():
    """Manually trigger a report generation."""
    global tracker_instance
    if not tracker_instance or not tracker_instance._running:
        return jsonify({"success": False, "error": "Tracker is not running"})
    
    try:
        report_path = tracker_instance._generate_report(datetime.now())
        return jsonify({"success": True, "message": "Report generated", "path": str(report_path)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/cleanup", methods=["POST"])
def api_cleanup():
    """Run cleanup manually."""
    from tracker.cleanup import cleanup_old_files
    try:
        removed = cleanup_old_files()
        return jsonify({"success": True, "removed": removed})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/processes")
def api_processes():
    """Get current running processes."""
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                pinfo = proc.info
                processes.append({
                    "pid": pinfo["pid"],
                    "name": pinfo["name"],
                    "cpu": round(pinfo["cpu_percent"] or 0, 1),
                    "memory": round(pinfo["memory_percent"] or 0, 1),
                })
            except Exception:
                continue
        processes.sort(key=lambda x: -x["cpu"])
        return jsonify(processes[:50])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/network")
def api_network():
    """Get current network connections."""
    try:
        import psutil
        connections = []
        for conn in psutil.net_connections(kind="inet"):
            try:
                if conn.status == "ESTABLISHED" and conn.raddr:
                    connections.append({
                        "pid": conn.pid,
                        "local": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                        "remote": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                        "status": conn.status,
                    })
            except Exception:
                continue
        return jsonify(connections[:50])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stream")
def api_stream():
    """Server-Sent Events for live updates."""
    def generate():
        while True:
            try:
                data = {
                    "status": get_tracker_status(),
                    "activity": get_activity_summary(),
                    "disk": get_disk_usage(),
                }
                yield f"data: {json.dumps(data)}\n\n"
            except Exception:
                pass
            time.sleep(5)
    
    return Response(generate(), mimetype="text/event-stream")


def run_dashboard(host="127.0.0.1", port=5000, debug=False):
    """Run the dashboard server."""
    log.info(f"Dashboard starting at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    run_dashboard()