"""Entry point for the Daily Tracker."""
import sys
import os

# Ensure the tracker package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracker.main import main

if __name__ == "__main__":
    main()