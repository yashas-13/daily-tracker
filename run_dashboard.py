"""Entry point for the Daily Tracker Dashboard."""
import sys
import os
import webbrowser
import threading

# Ensure the tracker package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.app import app, run_dashboard
from tracker.logger import log


def main():
    """Run the dashboard server and open the browser."""
    host = "127.0.0.1"
    port = 5000
    
    # Open browser in a separate thread after a short delay
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(f"http://{host}:{port}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    log.info(f"Dashboard starting at http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()