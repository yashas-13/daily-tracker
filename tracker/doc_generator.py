"""Generates detailed Markdown documentation from collected tracking data."""
import json
from datetime import datetime
from pathlib import Path

from . import config
from .logger import log


class DocGenerator:
    """Generates detailed Markdown reports every interval."""

    def __init__(self):
        self._session_start = datetime.now()

    def _format_duration(self, seconds: int) -> str:
        """Format seconds into a human-readable duration."""
        if seconds < 60:
            return f"{seconds}s"
        minutes, sec = divmod(seconds, 60)
        if minutes < 60:
            return f"{minutes}m {sec}s"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m {sec}s"

    def _build_key_log_section(self, key_log: list) -> str:
        """Build a readable keystroke log section."""
        if not key_log:
            return "_No keyboard activity recorded in this interval._\n"

        lines = []
        # Group consecutive keys into "typing sessions" for readability
        current_session = []
        last_time = None

        for ts, key, event in key_log:
            if event != "press":
                continue
            if last_time and (ts - last_time).total_seconds() > 5:
                # Break session
                if current_session:
                    session_text = "".join(current_session)
                    lines.append(f"- **Typing session:** `{session_text}`")
                current_session = []
            current_session.append(key)
            last_time = ts

        if current_session:
            session_text = "".join(current_session)
            lines.append(f"- **Typing session:** `{session_text}`")

        if not lines:
            lines.append("_No printable keystrokes recorded._")

        return "\n".join(lines) + "\n"

    def _build_mouse_log_section(self, mouse_log: list) -> str:
        """Build a mouse activity section."""
        if not mouse_log:
            return "_No mouse activity recorded in this interval._\n"

        clicks = [m for m in mouse_log if "click" in m[3]]
        moves = [m for m in mouse_log if m[3] == "move"]
        scrolls = [m for m in mouse_log if "scroll" in m[3]]

        lines = [
            f"- **Total mouse events:** {len(mouse_log)}",
            f"- **Mouse moves:** {len(moves)}",
            f"- **Clicks:** {len(clicks)}",
            f"- **Scrolls:** {len(scrolls)}",
        ]

        if clicks:
            lines.append("\n**Click details:**")
            for ts, x, y, action in clicks[:50]:
                lines.append(f"  - `{ts.strftime('%H:%M:%S')}` - {action} at ({x}, {y})")

        return "\n".join(lines) + "\n"

    def _build_window_section(self, window_summary: dict) -> str:
        """Build the active window/app usage section."""
        if not window_summary:
            return "_No window activity recorded._\n"

        lines = [
            f"- **Total samples:** {window_summary.get('total_samples', 0)}",
            f"- **Estimated active duration:** {self._format_duration(window_summary.get('estimated_duration_seconds', 0))}",
        ]

        top_processes = window_summary.get("top_processes", [])
        if top_processes:
            lines.append("\n**Top applications used:**")
            lines.append("| Application | Samples | Est. Time | % of Interval |")
            lines.append("|------------|---------|-----------|---------------|")
            for p in top_processes:
                lines.append(
                    f"| {p['process']} | {p['samples']} | "
                    f"{self._format_duration(p['estimated_seconds'])} | {p['percentage']}% |"
                )

        top_windows = window_summary.get("top_windows", [])
        if top_windows:
            lines.append("\n**Top window titles:**")
            for w in top_windows:
                lines.append(f"- `{w['title']}` - {self._format_duration(w['estimated_seconds'])}")

        return "\n".join(lines) + "\n"

    def _build_process_section(self, process_summary: dict) -> str:
        """Build the running processes section."""
        if not process_summary:
            return "_No process data recorded._\n"

        lines = [
            f"- **Total snapshots:** {process_summary.get('total_snapshots', 0)}",
        ]

        processes = process_summary.get("processes", [])
        if processes:
            lines.append("\n**Running processes (top 30 by activity):**")
            lines.append("| Process | Snapshots | Max CPU % | Max Mem % | Command Line |")
            lines.append("|---------|-----------|-----------|-----------|--------------|")
            for p in processes:
                cmd = (p.get("command_lines") or [""])[0]
                if len(cmd) > 80:
                    cmd = cmd[:77] + "..."
                lines.append(
                    f"| {p['process']} | {p['snapshots_seen']} | "
                    f"{p['max_cpu_percent']} | {p['max_memory_percent']} | `{cmd}` |"
                )

        return "\n".join(lines) + "\n"

    def _build_network_section(self, network_summary: dict) -> str:
        """Build the network/API activity section."""
        if not network_summary:
            return "_No network activity recorded._\n"

        lines = [
            f"- **Total snapshots:** {network_summary.get('total_snapshots', 0)}",
        ]

        endpoints = network_summary.get("top_remote_endpoints", [])
        if endpoints:
            lines.append("\n**Top remote endpoints (API/network connections):**")
            lines.append("| Endpoint | Connections |")
            lines.append("|----------|-------------|")
            for ep in endpoints:
                lines.append(f"| `{ep['endpoint']}` | {ep['connections']} |")

        return "\n".join(lines) + "\n"

    def _build_screenshot_section(self, screenshots: list) -> str:
        """Build the screenshots section."""
        if not screenshots:
            return "_No screenshots captured in this interval._\n"

        lines = [f"- **Screenshots captured:** {len(screenshots)}"]
        for ts, path in screenshots:
            rel_path = path.relative_to(config.DATA_DIR)
            lines.append(f"  - `{ts.strftime('%H:%M:%S')}` - `{rel_path}`")

        return "\n".join(lines) + "\n"

    def _build_key_summary_section(self, key_summary: dict) -> str:
        """Build the keystroke summary section."""
        if not key_summary or key_summary.get("total_keys", 0) == 0:
            return "_No keystrokes recorded._\n"

        lines = [f"- **Total keystrokes:** {key_summary['total_keys']}"]
        top_keys = key_summary.get("top_keys", [])
        if top_keys:
            lines.append("\n**Most frequent keys:**")
            for key, count in top_keys[:20]:
                display = key if key != " " else "SPACE"
                lines.append(f"- `{display}`: {count}")

        return "\n".join(lines) + "\n"

    def _build_mouse_summary_section(self, mouse_summary: dict) -> str:
        """Build the mouse summary section."""
        if not mouse_summary or mouse_summary.get("total_events", 0) == 0:
            return "_No mouse activity recorded._\n"

        lines = [f"- **Total mouse events:** {mouse_summary['total_events']}"]
        top_events = mouse_summary.get("top_events", [])
        if top_events:
            lines.append("\n**Event breakdown:**")
            for event, count in top_events[:15]:
                lines.append(f"- `{event}`: {count}")

        return "\n".join(lines) + "\n"

    def generate(
        self,
        interval_start: datetime,
        interval_end: datetime,
        window_log: list,
        window_summary: dict,
        key_log: list,
        key_summary: dict,
        mouse_log: list,
        mouse_summary: dict,
        process_snapshots: list,
        process_summary: dict,
        network_snapshots: list,
        network_summary: dict,
        screenshots: list,
    ) -> Path:
        """Generate a detailed Markdown report for the interval."""
        date_str = interval_start.strftime("%Y-%m-%d")
        time_str = interval_start.strftime("%H%M")
        filename = f"report_{date_str}_{time_str}.md"
        filepath = config.DOCS_DIR / filename

        duration = (interval_end - interval_start).total_seconds()

        # Build the report
        report = []
        report.append(f"# Daily Activity Report - {interval_start.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append(f"> **Interval:** {interval_start.strftime('%H:%M:%S')} - {interval_end.strftime('%H:%M:%S')}")
        report.append(f"> **Duration:** {self._format_duration(int(duration))}")
        report.append(f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("---")
        report.append("")

        # 1. Summary
        report.append("## 📊 Interval Summary")
        report.append("")
        report.append(f"- **Active windows sampled:** {len(window_log)}")
        report.append(f"- **Keystrokes:** {key_summary.get('total_keys', 0)}")
        report.append(f"- **Mouse events:** {mouse_summary.get('total_events', 0)}")
        report.append(f"- **Process snapshots:** {len(process_snapshots)}")
        report.append(f"- **Network snapshots:** {len(network_snapshots)}")
        report.append(f"- **Screenshots:** {len(screenshots)}")
        report.append("")
        report.append("---")
        report.append("")

        # 2. Applications / Windows
        report.append("## 🖥️ Applications & Windows Used")
        report.append("")
        report.append(self._build_window_section(window_summary))
        report.append("")
        report.append("---")
        report.append("")

        # 3. Keystrokes
        report.append("## ⌨️ Keystroke Activity")
        report.append("")
        report.append(self._build_key_summary_section(key_summary))
        report.append("")
        report.append("### Detailed Keystroke Log")
        report.append("")
        report.append(self._build_key_log_section(key_log))
        report.append("")
        report.append("---")
        report.append("")

        # 4. Mouse
        report.append("## 🖱️ Mouse Activity")
        report.append("")
        report.append(self._build_mouse_summary_section(mouse_summary))
        report.append("")
        report.append("### Detailed Mouse Log")
        report.append("")
        report.append(self._build_mouse_log_section(mouse_log))
        report.append("")
        report.append("---")
        report.append("")

        # 5. Processes
        report.append("## ⚙️ Running Processes")
        report.append("")
        report.append(self._build_process_section(process_summary))
        report.append("")
        report.append("---")
        report.append("")

        # 6. Network / API
        report.append("## 🌐 Network & API Activity")
        report.append("")
        report.append(self._build_network_section(network_summary))
        report.append("")
        report.append("---")
        report.append("")

        # 7. Screenshots
        report.append("## 📸 Screenshots")
        report.append("")
        report.append(self._build_screenshot_section(screenshots))
        report.append("")
        report.append("---")
        report.append("")

        # 8. Raw data reference
        report.append("## 📁 Raw Data")
        report.append("")
        report.append("Raw tracking data is stored in the `data/raw/` directory for deeper analysis.")
        report.append("")

        # Write the report
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(report))
            log.info(f"Report generated: {filepath}")
            return filepath
        except Exception as e:
            log.error(f"Failed to write report: {e}")
            return None

    def save_raw_data(self, interval_start: datetime, data: dict):
        """Save raw JSON data for the interval."""
        date_str = interval_start.strftime("%Y-%m-%d")
        time_str = interval_start.strftime("%H%M")
        filename = f"raw_{date_str}_{time_str}.json"
        filepath = config.RAW_DIR / filename
        try:
            # Convert datetime objects to strings for JSON serialization
            def serialize(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if isinstance(obj, Path):
                    return str(obj)
                return str(obj)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=serialize)
            log.debug(f"Raw data saved: {filepath}")
        except Exception as e:
            log.error(f"Failed to save raw data: {e}")