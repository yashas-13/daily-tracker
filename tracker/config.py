"""Configuration for the Daily Tracker."""
import os
import json
from pathlib import Path

# Base directory - where the tracker is installed
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory - where all logs, screenshots, and docs are stored
DATA_DIR = Path(os.environ.get("TRACKER_DATA_DIR", str(BASE_DIR / "data")))

# Subdirectories
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
DOCS_DIR = DATA_DIR / "docs"
LOGS_DIR = DATA_DIR / "logs"
RAW_DIR = DATA_DIR / "raw"

# Interval in minutes for documentation generation
INTERVAL_MINUTES = 15

# Screenshot settings
SCREENSHOT_ENABLED = True
SCREENSHOT_INTERVAL_SECONDS = 60  # Capture a screenshot every 60 seconds for the 15-min window
SCREENSHOT_QUALITY = 85  # JPEG quality (0-100)

# Input tracking
KEYBOARD_ENABLED = True
MOUSE_ENABLED = True

# Process/network tracking
PROCESS_ENABLED = True
NETWORK_ENABLED = True

# Window tracking
WINDOW_ENABLED = True
WINDOW_SAMPLE_INTERVAL = 5  # seconds

# Max entries to keep in memory before flushing
MAX_BUFFER_SIZE = 10000

# Retention - how many days of data to keep
RETENTION_DAYS = 30

# Privacy - redact sensitive patterns (passwords, tokens, etc.)
REDACT_PATTERNS = [
    (r"(?i)(password|passwd|pwd)\s*[=:]\s*\S+", r"\1=***REDACTED***"),
    (r"(?i)(token|api[_-]?key|secret|auth)\s*[=:]\s*\S+", r"\1=***REDACTED***"),
    (r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/]+=*", r"\1***REDACTED***"),
]


def ensure_dirs():
    """Create all required directories."""
    for d in [SCREENSHOTS_DIR, DOCS_DIR, LOGS_DIR, RAW_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def load_config():
    """Load user config overrides from config.json if present."""
    config_file = BASE_DIR / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                overrides = json.load(f)
            for key, value in overrides.items():
                if key in globals() and key.isupper():
                    globals()[key] = value
        except Exception:
            pass


def save_config():
    """Save current config to config.json."""
    config_file = BASE_DIR / "config.json"
    config = {
        "INTERVAL_MINUTES": INTERVAL_MINUTES,
        "SCREENSHOT_ENABLED": SCREENSHOT_ENABLED,
        "SCREENSHOT_INTERVAL_SECONDS": SCREENSHOT_INTERVAL_SECONDS,
        "KEYBOARD_ENABLED": KEYBOARD_ENABLED,
        "MOUSE_ENABLED": MOUSE_ENABLED,
        "PROCESS_ENABLED": PROCESS_ENABLED,
        "NETWORK_ENABLED": NETWORK_ENABLED,
        "WINDOW_ENABLED": WINDOW_ENABLED,
        "RETENTION_DAYS": RETENTION_DAYS,
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# Initialize
ensure_dirs()
load_config()