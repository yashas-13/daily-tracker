"""MCP Server entry point for Daily Tracker.

Usage:
    python run_mcp.py                    # stdio (for MCP clients like Claude Desktop)
    python run_mcp.py --transport sse    # SSE mode (HTTP endpoint)

Stdio mode is used by most AI coding tools (Claude Desktop, Cursor, Windsurf, etc.)
SSE mode is for HTTP-based clients and remote access.
"""
import sys
import argparse

sys.path.insert(0, ".")

from tracker.mcp_server import run_stdio, run_sse


def main():
    parser = argparse.ArgumentParser(description="Daily Tracker MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="SSE host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="SSE port (default: 8080)")
    args = parser.parse_args()

    if args.transport == "sse":
        run_sse(host=args.host, port=args.port)
    else:
        run_stdio()


if __name__ == "__main__":
    main()