"""Main orchestrator for the Daily Tracker."""
import time
import threading
from datetime import datetime, timedelta

from . import config
from .logger import log
from .screenshot import ScreenshotManager
from .window_tracker import WindowTracker
from .input_tracker import InputTracker
from .process_tracker import ProcessTracker
from .doc_generator import DocGenerator
from .cleanup import run_cleanup_loop


class DailyTracker:
    """Orchestrates all tracking modules and generates reports every 15 minutes."""

    def __init__(self):
        self.screenshots = ScreenshotManager()
        self.windows = WindowTracker()
        self.inputs = InputTracker()
        self.processes = ProcessTracker()
        self.doc_gen = DocGenerator()

        self._stop = threading.Event()
        self._main_thread = None
        self._snapshot_thread = None
        self._cleanup_thread = None
        self._running = False

    def _snapshot_loop(self):
        """Background loop that takes process/network snapshots periodically."""
        log.info("Snapshot thread started.")
        while not self._stop.is_set():
            self.processes.snapshot()
            self._stop.wait(30)  # Snapshot every 30 seconds
        log.info("Snapshot thread stopped.")

    def _generate_report(self, interval_start: datetime):
        """Collect all data and generate a report for the interval."""
        interval_end = datetime.now()
        log.info(f"Generating report for interval {interval_start} - {interval_end}")

        # Collect data from all trackers
        window_log = self.windows.get_window_log()
        window_summary = self.windows.summarize(window_log)

        key_log = self.inputs.get_key_log()
        key_summary = self.inputs.get_key_summary()

        mouse_log = self.inputs.get_mouse_log()
        mouse_summary = self.inputs.get_mouse_summary()

        process_snapshots = self.processes.get_process_snapshots()
        process_summary = self.processes.summarize_processes(process_snapshots)

        network_snapshots = self.processes.get_network_snapshots()
        network_summary = self.processes.summarize_network(network_snapshots)

        screenshots = self.screenshots.get_screenshots()

        # Generate the report
        report_path = self.doc_gen.generate(
            interval_start=interval_start,
            interval_end=interval_end,
            window_log=window_log,
            window_summary=window_summary,
            key_log=key_log,
            key_summary=key_summary,
            mouse_log=mouse_log,
            mouse_summary=mouse_summary,
            process_snapshots=process_snapshots,
            process_summary=process_summary,
            network_snapshots=network_snapshots,
            network_summary=network_summary,
            screenshots=screenshots,
        )

        # Save raw data
        raw_data = {
            "interval_start": interval_start,
            "interval_end": interval_end,
            "window_log": window_log,
            "window_summary": window_summary,
            "key_log": key_log,
            "key_summary": key_summary,
            "mouse_log": mouse_log,
            "mouse_summary": mouse_summary,
            "process_snapshots": process_snapshots,
            "process_summary": process_summary,
            "network_snapshots": network_snapshots,
            "network_summary": network_summary,
            "screenshots": [(ts.isoformat(), str(p)) for ts, p in screenshots],
        }
        self.doc_gen.save_raw_data(interval_start, raw_data)

        return report_path

    def _main_loop(self):
        """Main loop that runs every 15 minutes."""
        log.info(f"Daily Tracker started. Reports every {config.INTERVAL_MINUTES} minutes.")
        interval_start = datetime.now()

        while not self._stop.is_set():
            # Wait for the interval duration
            self._stop.wait(config.INTERVAL_MINUTES * 60)

            if self._stop.is_set():
                break

            try:
                self._generate_report(interval_start)
            except Exception as e:
                log.error(f"Error generating report: {e}")

            interval_start = datetime.now()

        # Generate a final report on shutdown
        try:
            self._generate_report(interval_start)
        except Exception as e:
            log.error(f"Error generating final report: {e}")

        log.info("Daily Tracker stopped.")

    def start(self):
        """Start all tracking modules and the main loop."""
        if self._running:
            return
        self._running = True
        self._stop.clear()

        # Start all trackers
        self.screenshots.start()
        self.windows.start()
        self.inputs.start()

        # Start snapshot thread
        self._snapshot_thread = threading.Thread(
            target=self._snapshot_loop, daemon=True, name="snapshot-thread"
        )
        self._snapshot_thread.start()

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=run_cleanup_loop, args=(self._stop,), daemon=True, name="cleanup-thread"
        )
        self._cleanup_thread.start()

        # Start main loop
        self._main_thread = threading.Thread(
            target=self._main_loop, daemon=True, name="main-thread"
        )
        self._main_thread.start()

        log.info("All tracking modules started.")

    def stop(self):
        """Stop all tracking modules."""
        if not self._running:
            return
        self._running = False
        self._stop.set()

        # Stop all trackers
        self.screenshots.stop()
        self.windows.stop()
        self.inputs.stop()

        if self._snapshot_thread:
            self._snapshot_thread.join(timeout=5)
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        if self._main_thread:
            self._main_thread.join(timeout=10)

        log.info("All tracking modules stopped.")

    def run_forever(self):
        """Run the tracker in the foreground (blocking)."""
        self.start()
        try:
            while not self._stop.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Keyboard interrupt received.")
            self.stop()


def main():
    """Entry point."""
    tracker = DailyTracker()
    tracker.run_forever()


if __name__ == "__main__":
    main()