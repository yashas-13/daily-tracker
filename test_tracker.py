"""Quick test script - runs the tracker for a few seconds and generates a test report."""
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracker.main import DailyTracker
from tracker import config
from tracker.logger import log

# Use a short interval for testing
config.INTERVAL_MINUTES = 0.1  # 6 seconds

def main():
    print("=" * 60)
    print("Daily Tracker - Quick Test")
    print("=" * 60)
    print()

    tracker = DailyTracker()
    tracker.start()

    print("Tracker started. Collecting data for 10 seconds...")
    time.sleep(10)

    print("\nGenerating test report...")
    interval_start = datetime.now()
    # Manually trigger a report
    report_path = tracker._generate_report(interval_start)

    print("\nStopping tracker...")
    tracker.stop()

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    print(f"Report generated: {report_path}")
    print()
    print("Data directories:")
    print(f"  Docs: {config.DOCS_DIR}")
    print(f"  Screenshots: {config.SCREENSHOTS_DIR}")
    print(f"  Logs: {config.LOGS_DIR}")
    print(f"  Raw: {config.RAW_DIR}")
    print()

    # List generated files
    print("Generated files:")
    for d in [config.DOCS_DIR, config.SCREENSHOTS_DIR, config.RAW_DIR]:
        if d.exists():
            files = list(d.iterdir())
            if files:
                print(f"  {d.name}/:")
                for f in files[:5]:
                    print(f"    - {f.name}")
            else:
                print(f"  {d.name}/: (empty)")

if __name__ == "__main__":
    main()