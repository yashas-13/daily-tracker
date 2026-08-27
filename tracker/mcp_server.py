"""MCP Server for Daily Tracker - exposes tracker data/control to AI agents.

Supports all providers via standard MCP protocol (stdio transport):
- Claude Desktop / Claude Code
- Cursor / Windsurf
- OpenAI Codex / ChatGPT
- Google Gemini / Jules
- Any MCP-compatible client

Usage:
    python run_mcp.py                    # stdio mode (for MCP clients)
    python run_mcp.py --transport sse    # SSE mode (for HTTP clients)
"""
import os
import sys
import json
import glob
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tracker import config
from tracker.logger import log
from tracker.main import DailyTracker

# Global tracker instance (shared with server)
_tracker: Optional[DailyTracker] = None


def _get_tracker() -> DailyTracker:
    global _tracker
    if _tracker is None:
        _tracker = DailyTracker()
    return _tracker


def _list_reports(limit: int = 20) -> list[dict]:
    """List recent report files."""
    docs_dir = config.DOCS_DIR
    if not docs_dir.exists():
        return []
    files = sorted(docs_dir.glob("*.md"), reverse=True)[:limit]
    results = []
    for f in files:
        stat = f.stat()
        results.append({
            "filename": f.name,
            "path": str(f),
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return results


def _read_report(filename: str) -> str:
    """Read a report file's content."""
    path = config.DOCS_DIR / filename
    if not path.exists():
        # Try partial match
        matches = list(config.DOCS_DIR.glob(f"*{filename}*"))
        if not matches:
            return f"Report not found: {filename}"
        path = matches[0]
    return path.read_text(encoding="utf-8")


def _list_screenshots(limit: int = 20) -> list[dict]:
    """List recent screenshot files."""
    ss_dir = config.SCREENSHOTS_DIR
    if not ss_dir.exists():
        return []
    files = sorted(ss_dir.glob("*.jpg"), reverse=True)[:limit]
    return [{"filename": f.name, "path": str(f), "size_bytes": f.stat().st_size} for f in files]


def _get_raw_data(filename: str) -> dict:
    """Read raw JSON data file."""
    path = config.RAW_DIR / filename
    if not path.exists():
        matches = list(config.RAW_DIR.glob(f"*{filename}*"))
        if not matches:
            return {"error": f"Raw data not found: {filename}"}
        path = matches[0]
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _list_raw_data(limit: int = 20) -> list[dict]:
    """List raw data files."""
    raw_dir = config.RAW_DIR
    if not raw_dir.exists():
        return []
    files = sorted(raw_dir.glob("*.json"), reverse=True)[:limit]
    return [{"filename": f.name, "path": str(f), "size_bytes": f.stat().st_size} for f in files]


def _get_live_status() -> dict:
    """Get current tracker status and live data."""
    tracker = _get_tracker()
    return {
        "running": tracker._running,
        "config": {
            "interval_minutes": config.INTERVAL_MINUTES,
            "screenshot_enabled": config.SCREENSHOT_ENABLED,
            "screenshot_interval": config.SCREENSHOT_INTERVAL_SECONDS,
            "keyboard_enabled": config.KEYBOARD_ENABLED,
            "mouse_enabled": config.MOUSE_ENABLED,
            "process_enabled": config.PROCESS_ENABLED,
            "network_enabled": config.NETWORK_ENABLED,
            "window_enabled": config.WINDOW_ENABLED,
            "retention_days": config.RETENTION_DAYS,
        },
        "data_dirs": {
            "docs": str(config.DOCS_DIR),
            "screenshots": str(config.SCREENSHOTS_DIR),
            "raw": str(config.RAW_DIR),
            "logs": str(config.LOGS_DIR),
        },
        "report_count": len(list(config.DOCS_DIR.glob("*.md"))) if config.DOCS_DIR.exists() else 0,
        "screenshot_count": len(list(config.SCREENSHOTS_DIR.glob("*.jpg"))) if config.SCREENSHOTS_DIR.exists() else 0,
        "raw_data_count": len(list(config.RAW_DIR.glob("*.json"))) if config.RAW_DIR.exists() else 0,
    }


def _search_activity(query: str, days: int = 7) -> list[dict]:
    """Search through reports for activity matching a query."""
    results = []
    docs_dir = config.DOCS_DIR
    if not docs_dir.exists():
        return results

    cutoff = datetime.now() - timedelta(days=days)
    for f in sorted(docs_dir.glob("*.md"), reverse=True):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            break
        content = f.read_text(encoding="utf-8")
        if query.lower() in content.lower():
            # Find matching lines
            matches = []
            for i, line in enumerate(content.split("\n"), 1):
                if query.lower() in line.lower():
                    matches.append({"line": i, "text": line.strip()})
            results.append({
                "filename": f.name,
                "date": mtime.strftime("%Y-%m-%d"),
                "matches": matches[:10],
            })
    return results


def _get_process_summary(days: int = 1) -> dict:
    """Get process usage summary from raw data."""
    raw_dir = config.RAW_DIR
    if not raw_dir.exists():
        return {"error": "No data directory"}

    process_time = {}
    cutoff = datetime.now() - timedelta(days=days)

    for f in sorted(raw_dir.glob("*.json"), reverse=True):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            break
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for snap in data.get("process_snapshots", []):
                for proc in snap.get("processes", [])[:50]:
                    name = proc.get("name", "unknown")
                    if name not in process_time:
                        process_time[name] = {"snapshots": 0, "max_cpu": 0, "max_mem": 0}
                    process_time[name]["snapshots"] += 1
                    process_time[name]["max_cpu"] = max(process_time[name]["max_cpu"], proc.get("cpu_percent", 0))
                    process_time[name]["max_mem"] = max(process_time[name]["max_mem"], proc.get("memory_percent", 0))
        except Exception:
            continue

    # Sort by activity
    sorted_procs = sorted(process_time.items(), key=lambda x: x[1]["snapshots"], reverse=True)[:30]
    return {"period_days": days, "top_processes": dict(sorted_procs)}


def _get_network_summary(days: int = 1) -> dict:
    """Get network activity summary."""
    raw_dir = config.RAW_DIR
    if not raw_dir.exists():
        return {"error": "No data directory"}

    endpoints = {}
    cutoff = datetime.now() - timedelta(days=days)

    for f in sorted(raw_dir.glob("*.json"), reverse=True):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            break
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for snap in data.get("network_snapshots", []):
                for conn in snap.get("connections", []):
                    ep = conn.get("remote_address", "unknown")
                    if ep not in endpoints:
                        endpoints[ep] = 0
                    endpoints[ep] += 1
        except Exception:
            continue

    sorted_eps = sorted(endpoints.items(), key=lambda x: x[1], reverse=True)[:30]
    return {"period_days": days, "top_endpoints": dict(sorted_eps)}


# ─── MCP Server Setup ───────────────────────────────────────────────────

server = Server("daily-tracker")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools for AI agents."""
    return [
        Tool(
            name="get_tracker_status",
            description="Get current tracker status: running state, config, data counts. Use to check if tracker is active.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="list_reports",
            description="List recent activity reports (Markdown docs generated every 15 min). Returns filename, date, size.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max reports to return (default 20)", "default": 20},
                },
            },
        ),
        Tool(
            name="get_report",
            description="Read full content of a specific activity report. Contains: apps used, keystrokes, mouse clicks, processes, network, screenshots.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Report filename (e.g. 'report_2026-08-26_1340.md') or date prefix"},
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="list_screenshots",
            description="List recent screenshot captures. Returns filename, path, size.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max screenshots (default 20)", "default": 20},
                },
            },
        ),
        Tool(
            name="get_screenshot",
            description="Get a specific screenshot as base64 image for visual inspection.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Screenshot filename (e.g. '20260826_134024.jpg')"},
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="search_activity",
            description="Search through all reports for specific activity. Find what apps, files, or actions match a query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term (e.g. 'chrome', 'python', 'slack')"},
                    "days": {"type": "integer", "description": "Search last N days (default 7)", "default": 7},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_process_summary",
            description="Get process usage summary: which apps used most, CPU/memory peaks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Summarize last N days (default 1)", "default": 1},
                },
            },
        ),
        Tool(
            name="get_network_summary",
            description="Get network activity summary: top endpoints, API calls, connections.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Summarize last N days (default 1)", "default": 1},
                },
            },
        ),
        Tool(
            name="list_raw_data",
            description="List raw JSON data files available for deep analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max files (default 20)", "default": 20},
                },
            },
        ),
        Tool(
            name="get_raw_data",
            description="Get raw tracking data JSON: all window logs, keystrokes, processes, network for a specific interval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Raw data filename (e.g. 'raw_2026-08-26_1340.json')"},
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="generate_report_now",
            description="Force-generate an activity report immediately (normally auto-generated every 15 min).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_activity_summary",
            description="Get a concise natural-language summary of recent activity across all reports. Best for quick overviews.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {"type": "integer", "description": "Summarize last N hours (default 1)", "default": 1},
                },
            },
        ),
        Tool(
            name="export_data",
            description="Export all tracker data as a single JSON bundle for external processing or backup.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Export last N days (default 1)", "default": 1},
                },
            },
        ),
    ]


@server.list_resources()
async def list_resources():
    """List MCP resources (data sources)."""
    from mcp.types import Resource, ResourceTemplate
    return [
        Resource(
            uri="daily-tracker://status",
            name="Tracker Status",
            description="Current tracker running state and configuration",
            mimeType="application/json",
        ),
        Resource(
            uri="daily-tracker://config",
            name="Tracker Config",
            description="Current tracker configuration",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read MCP resources."""
    if uri == "daily-tracker://status":
        return json.dumps(_get_live_status(), indent=2, default=str)
    elif uri == "daily-tracker://config":
        return json.dumps({
            "INTERVAL_MINUTES": config.INTERVAL_MINUTES,
            "SCREENSHOT_ENABLED": config.SCREENSHOT_ENABLED,
            "SCREENSHOT_INTERVAL_SECONDS": config.SCREENSHOT_INTERVAL_SECONDS,
            "KEYBOARD_ENABLED": config.KEYBOARD_ENABLED,
            "MOUSE_ENABLED": config.MOUSE_ENABLED,
            "PROCESS_ENABLED": config.PROCESS_ENABLED,
            "NETWORK_ENABLED": config.NETWORK_ENABLED,
            "WINDOW_ENABLED": config.WINDOW_ENABLED,
            "RETENTION_DAYS": config.RETENTION_DAYS,
        }, indent=2)
    raise ValueError(f"Unknown resource: {uri}")


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    """Handle tool calls from AI agents."""
    try:
        if name == "get_tracker_status":
            result = _get_live_status()
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "list_reports":
            limit = arguments.get("limit", 20)
            result = _list_reports(limit)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "get_report":
            content = _read_report(arguments["filename"])
            return [TextContent(type="text", text=content)]

        elif name == "list_screenshots":
            limit = arguments.get("limit", 20)
            result = _list_screenshots(limit)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_screenshot":
            filename = arguments["filename"]
            path = config.SCREENSHOTS_DIR / filename
            if not path.exists():
                matches = list(config.SCREENSHOTS_DIR.glob(f"*{filename}*"))
                if matches:
                    path = matches[0]
                else:
                    return [TextContent(type="text", text=f"Screenshot not found: {filename}")]
            import base64
            img_data = path.read_bytes()
            b64 = base64.b64encode(img_data).decode("ascii")
            return [ImageContent(type="image", data=b64, mimeType="image/jpeg")]

        elif name == "search_activity":
            query = arguments["query"]
            days = arguments.get("days", 7)
            result = _search_activity(query, days)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "get_process_summary":
            days = arguments.get("days", 1)
            result = _get_process_summary(days)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "get_network_summary":
            days = arguments.get("days", 1)
            result = _get_network_summary(days)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "list_raw_data":
            limit = arguments.get("limit", 20)
            result = _list_raw_data(limit)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_raw_data":
            result = _get_raw_data(arguments["filename"])
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "generate_report_now":
            tracker = _get_tracker()
            from datetime import datetime
            start = datetime.now() - timedelta(minutes=config.INTERVAL_MINUTES)
            report_path = tracker._generate_report(start)
            return [TextContent(type="text", text=f"Report generated: {report_path}")]

        elif name == "get_activity_summary":
            hours = arguments.get("hours", 1)
            reports = _list_reports(100)
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            recent = [r for r in reports if r["modified"] >= cutoff]

            summary_parts = []
            for r in recent[:4]:
                content = _read_report(r["filename"])
                # Extract summary section
                lines = content.split("\n")
                in_summary = False
                summary_lines = []
                for line in lines:
                    if "Interval Summary" in line:
                        in_summary = True
                        continue
                    if in_summary:
                        if line.startswith("---"):
                            break
                        if line.strip():
                            summary_lines.append(line.strip())
                if summary_lines:
                    summary_parts.append(f"**{r['filename']}:**\n" + "\n".join(summary_lines))

            if not summary_parts:
                return [TextContent(type="text", text=f"No reports found in the last {hours} hour(s).")]

            return [TextContent(type="text", text=f"Activity Summary (last {hours}h):\n\n" + "\n\n".join(summary_parts))]

        elif name == "export_data":
            days = arguments.get("days", 1)
            cutoff = datetime.now() - timedelta(days=days)
            export = {
                "export_date": datetime.now().isoformat(),
                "period_days": days,
                "reports": [],
                "raw_data": [],
            }

            for r in _list_reports(100):
                if r["modified"] >= cutoff.isoformat():
                    export["reports"].append({
                        "filename": r["filename"],
                        "content": _read_report(r["filename"]),
                    })

            for rd in _list_raw_data(100):
                if rd.get("path", ""):
                    try:
                        with open(rd["path"], "r", encoding="utf-8") as f:
                            export["raw_data"].append(json.load(f))
                    except Exception:
                        pass

            return [TextContent(type="text", text=json.dumps(export, indent=2, default=str))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run_stdio():
    """Entry point for stdio mode."""
    asyncio.run(main())


def run_sse(host: str = "127.0.0.1", port: int = 8080):
    """Entry point for SSE/HTTP mode."""
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    log.info(f"MCP SSE server running on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_stdio()