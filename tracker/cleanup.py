"""Retention cleanup - removes old data files."""
import time
from datetime import datetime, timedelta
from pathlib import Path

from . import config
from .logger import log


def cleanup_old_files():
    """Remove files older than RETENTION_DAYS from data directories."""
    cutoff = datetime.now() - timedelta(days=config.RETENTION_DAYS)
    cutoff_ts = cutoff.timestamp()
    removed = 0

    for directory in [config.SCREENSHOTS_DIR, config.DOCS_DIR, config.RAW_DIR]:
        if not directory.exists():
            continue
        for filepath in directory.iterdir():
            try:
                if filepath.is_file() and filepath.stat().st_mtime < cutoff_ts:
                    filepath.unlink()
                    removed += 1
            except Exception as e:
                log.debug(f"Failed to remove {filepath}: {e}")

    if removed:
        log.info(f"Cleanup: removed {removed} old files (older than {config.RETENTION_DAYS} days).")
    return removed


def run_cleanup_loop(stop_event):
    """Background loop that runs cleanup periodically (every 6 hours)."""
    log.info("Cleanup thread started.")
    while not stop_event.is_set():
        try:
            cleanup_old_files()
        except Exception as e:
            log.error(f"Cleanup error: {e}")
        stop_event.wait(6 * 60 * 60)  # Run every 6 hours
    log.info("Cleanup thread stopped.")