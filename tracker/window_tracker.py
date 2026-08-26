"""Active window tracking using Windows API."""
import time
import threading
from datetime import datetime
from collections import Counter

from . import config
from .logger import log

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    log.warning("pywin32 not installed. Window tracking disabled.")


class WindowTracker:
    """Tracks the active foreground window and its process."""

    def __init__(self):
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._window_log = []  # List of (timestamp, title, process_name, pid)
        self._current = None

    def _get_foreground_window(self):
        """Get the foreground window title, process name, and PID."""
        if not HAS_WIN32:
            return None
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = ""
            try:
                handle = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                try:
                    import win32process as wp
                    process_name = wp.GetModuleFileNameEx(handle).split("\\")[-1]
                finally:
                    win32api.CloseHandle(handle)
            except Exception:
                process_name = f"PID {pid}"
            return {
                "title": title,
                "process": process_name,
                "pid": pid,
            }
        except Exception as e:
            log.debug(f"Error getting foreground window: {e}")
            return None

    def _run(self):
        """Background loop sampling the active window."""
        log.info("Window tracking thread started.")
        while not self._stop.is_set():
            info = self._get_foreground_window()
            if info:
                timestamp = datetime.now()
                with self._lock:
                    self._window_log.append((timestamp, info["title"], info["process"], info["pid"]))
                    self._current = info
            self._stop.wait(config.WINDOW_SAMPLE_INTERVAL)
        log.info("Window tracking thread stopped.")

    def start(self):
        """Start the window tracking thread."""
        if not config.WINDOW_ENABLED or not HAS_WIN32:
            log.info("Window tracking disabled.")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="window-thread")
        self._thread.start()

    def stop(self):
        """Stop the window tracking thread."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def get_current(self):
        """Return the current active window info."""
        with self._lock:
            return self._current

    def get_window_log(self) -> list:
        """Return the window log for the current interval and clear it."""
        with self._lock:
            log_entries = self._window_log
            self._window_log = []
        return log_entries

    def summarize(self, log_entries: list) -> dict:
        """Summarize window activity: most used apps, time per app, etc."""
        if not log_entries:
            return {}
        # Count time spent per process (approximate by sample count)
        process_counter = Counter()
        title_counter = Counter()
        for _, title, process, _ in log_entries:
            process_counter[process] += 1
            if title:
                title_counter[title] += 1

        total_samples = len(log_entries)
        sample_seconds = config.WINDOW_SAMPLE_INTERVAL

        summary = {
            "total_samples": total_samples,
            "estimated_duration_seconds": total_samples * sample_seconds,
            "top_processes": [
                {"process": proc, "samples": count, "estimated_seconds": count * sample_seconds,
                 "percentage": round(count / total_samples * 100, 1)}
                for proc, count in process_counter.most_common(15)
            ],
            "top_windows": [
                {"title": title, "samples": count, "estimated_seconds": count * sample_seconds}
                for title, count in title_counter.most_common(10)
            ],
        }
        return summary