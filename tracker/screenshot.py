"""Silent screenshot capture using mss."""
import time
import threading
from datetime import datetime
from pathlib import Path

from . import config
from .logger import log

try:
    import mss
    from PIL import Image
    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    log.warning("mss/Pillow not installed. Screenshot capture disabled.")


class ScreenshotManager:
    """Captures screenshots silently at a configurable interval."""

    def __init__(self):
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._screenshots = []  # List of (timestamp, filepath)
        self._sct = None

    def _init_mss(self):
        if HAS_MSS and self._sct is None:
            self._sct = mss.mss()

    def capture(self) -> Path | None:
        """Capture a single screenshot and save it. Returns the file path."""
        if not config.SCREENSHOT_ENABLED or not HAS_MSS:
            return None
        try:
            self._init_mss()
            timestamp = datetime.now()
            filename = timestamp.strftime("%Y%m%d_%H%M%S") + ".jpg"
            filepath = config.SCREENSHOTS_DIR / filename

            with self._lock:
                # Capture the primary monitor (or all monitors combined)
                monitor = self._sct.monitors[1]  # Primary monitor
                shot = self._sct.grab(monitor)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                img.save(filepath, "JPEG", quality=config.SCREENSHOT_QUALITY)

            self._screenshots.append((timestamp, filepath))
            log.debug(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            log.error(f"Screenshot capture failed: {e}")
            return None

    def _run(self):
        """Background loop that captures screenshots at the configured interval."""
        log.info("Screenshot capture thread started.")
        while not self._stop.is_set():
            self.capture()
            self._stop.wait(config.SCREENSHOT_INTERVAL_SECONDS)
        log.info("Screenshot capture thread stopped.")

    def start(self):
        """Start the background screenshot thread."""
        if not config.SCREENSHOT_ENABLED or not HAS_MSS:
            log.info("Screenshot capture disabled.")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="screenshot-thread")
        self._thread.start()

    def stop(self):
        """Stop the background screenshot thread."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def get_screenshots(self) -> list:
        """Return screenshots captured in the current interval and clear the buffer."""
        with self._lock:
            shots = self._screenshots
            self._screenshots = []
        return shots

    def get_latest(self) -> Path | None:
        """Return the most recent screenshot path."""
        with self._lock:
            if self._screenshots:
                return self._screenshots[-1][1]
        return None