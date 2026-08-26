"""Keyboard and mouse input tracking using pynput."""
import re
import threading
from datetime import datetime
from collections import Counter

from . import config
from .logger import log

try:
    from pynput import keyboard, mouse
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    log.warning("pynput not installed. Input tracking disabled.")


class InputTracker:
    """Tracks keyboard and mouse activity silently."""

    def __init__(self):
        self._lock = threading.Lock()
        self._key_log = []       # List of (timestamp, key_name, event_type)
        self._mouse_log = []     # List of (timestamp, x, y, event_type)
        self._key_counter = Counter()
        self._mouse_counter = Counter()
        self._keyboard_listener = None
        self._mouse_listener = None
        self._running = False

    def _redact(self, text: str) -> str:
        """Redact sensitive patterns from key text."""
        for pattern, replacement in config.REDACT_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

    def _on_key_press(self, key):
        try:
            timestamp = datetime.now()
            if hasattr(key, "char") and key.char is not None:
                key_name = key.char
            else:
                key_name = f"[{key.name}]" if hasattr(key, "name") else str(key)
            key_name = self._redact(key_name)
            with self._lock:
                self._key_log.append((timestamp, key_name, "press"))
                self._key_counter[key_name] += 1
        except Exception:
            pass

    def _on_key_release(self, key):
        try:
            timestamp = datetime.now()
            if hasattr(key, "char") and key.char is not None:
                key_name = key.char
            else:
                key_name = f"[{key.name}]" if hasattr(key, "name") else str(key)
            key_name = self._redact(key_name)
            with self._lock:
                self._key_log.append((timestamp, key_name, "release"))
        except Exception:
            pass

    def _on_mouse_move(self, x, y):
        try:
            timestamp = datetime.now()
            with self._lock:
                self._mouse_log.append((timestamp, x, y, "move"))
                self._mouse_counter["move"] += 1
        except Exception:
            pass

    def _on_mouse_click(self, x, y, button, pressed):
        try:
            timestamp = datetime.now()
            action = "click" if pressed else "release"
            with self._lock:
                self._mouse_log.append((timestamp, x, y, f"{action}:{button}"))
                self._mouse_counter[f"{action}:{button}"] += 1
        except Exception:
            pass

    def _on_mouse_scroll(self, x, y, dx, dy):
        try:
            timestamp = datetime.now()
            with self._lock:
                self._mouse_log.append((timestamp, x, y, f"scroll:{dx},{dy}"))
                self._mouse_counter["scroll"] += 1
        except Exception:
            pass

    def start(self):
        """Start keyboard and mouse listeners."""
        if not HAS_PYNPUT:
            log.info("Input tracking disabled (pynput not available).")
            return
        if self._running:
            return

        try:
            if config.KEYBOARD_ENABLED:
                self._keyboard_listener = keyboard.Listener(
                    on_press=self._on_key_press,
                    on_release=self._on_key_release,
                )
                self._keyboard_listener.daemon = True
                self._keyboard_listener.start()
                log.info("Keyboard listener started.")

            if config.MOUSE_ENABLED:
                self._mouse_listener = mouse.Listener(
                    on_move=self._on_mouse_move,
                    on_click=self._on_mouse_click,
                    on_scroll=self._on_mouse_scroll,
                )
                self._mouse_listener.daemon = True
                self._mouse_listener.start()
                log.info("Mouse listener started.")

            self._running = True
        except Exception as e:
            log.error(f"Failed to start input listeners: {e}")

    def stop(self):
        """Stop keyboard and mouse listeners."""
        self._running = False
        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
        log.info("Input listeners stopped.")

    def get_key_log(self) -> list:
        """Return the key log for the current interval and clear it."""
        with self._lock:
            entries = self._key_log
            self._key_log = []
        return entries

    def get_mouse_log(self) -> list:
        """Return the mouse log for the current interval and clear it."""
        with self._lock:
            entries = self._mouse_log
            self._mouse_log = []
        return entries

    def get_key_summary(self) -> dict:
        """Summarize key activity."""
        with self._lock:
            counter = self._key_counter.copy()
            self._key_counter.clear()
        return {
            "total_keys": sum(counter.values()),
            "top_keys": counter.most_common(30),
        }

    def get_mouse_summary(self) -> dict:
        """Summarize mouse activity."""
        with self._lock:
            counter = self._mouse_counter.copy()
            self._mouse_counter.clear()
        return {
            "total_events": sum(counter.values()),
            "top_events": counter.most_common(20),
        }