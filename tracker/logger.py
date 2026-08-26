"""Logging setup for the Daily Tracker."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import config


def setup_logger(name: str = "tracker") -> logging.Logger:
    """Set up and return a logger that writes to both file and console."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler with rotation (5 MB per file, keep 3 backups)
    log_file = config.LOGS_DIR / "tracker.log"
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Console handler (only if not running silently)
    if not getattr(sys, "frozen", False) and sys.stdout is not None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    return logger


# Default logger instance
log = setup_logger()