"""Process and network monitoring using psutil."""
import threading
from datetime import datetime

from . import config
from .logger import log

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    log.warning("psutil not installed. Process/network monitoring disabled.")


class ProcessTracker:
    """Monitors running processes and network connections."""

    def __init__(self):
        self._lock = threading.Lock()
        self._process_snapshots = []  # List of (timestamp, [process dicts])
        self._network_snapshots = []  # List of (timestamp, [connection dicts])

    def _get_processes(self) -> list:
        """Get a snapshot of running processes with command lines."""
        if not HAS_PSUTIL:
            return []
        processes = []
        try:
            for proc in psutil.process_iter(["pid", "name", "exe", "cmdline", "username", "cpu_percent", "memory_percent", "create_time"]):
                try:
                    pinfo = proc.info
                    processes.append({
                        "pid": pinfo["pid"],
                        "name": pinfo["name"],
                        "exe": pinfo["exe"],
                        "cmdline": " ".join(pinfo["cmdline"]) if pinfo["cmdline"] else "",
                        "username": pinfo["username"],
                        "cpu_percent": round(pinfo["cpu_percent"] or 0, 1),
                        "memory_percent": round(pinfo["memory_percent"] or 0, 1),
                        "create_time": datetime.fromtimestamp(pinfo["create_time"]).strftime("%Y-%m-%d %H:%M:%S") if pinfo["create_time"] else "",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            log.debug(f"Error getting processes: {e}")
        return processes

    def _get_network(self) -> list:
        """Get a snapshot of active network connections."""
        if not HAS_PSUTIL:
            return []
        connections = []
        try:
            for conn in psutil.net_connections(kind="inet"):
                try:
                    if conn.status == "ESTABLISHED" and conn.raddr:
                        connections.append({
                            "pid": conn.pid,
                            "local": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                            "remote": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                            "status": conn.status,
                        })
                except Exception:
                    continue
        except Exception as e:
            log.debug(f"Error getting network connections: {e}")
        return connections

    def snapshot(self):
        """Take a snapshot of processes and network connections."""
        if not HAS_PSUTIL:
            return
        timestamp = datetime.now()
        with self._lock:
            if config.PROCESS_ENABLED:
                self._process_snapshots.append((timestamp, self._get_processes()))
            if config.NETWORK_ENABLED:
                self._network_snapshots.append((timestamp, self._get_network()))

    def get_process_snapshots(self) -> list:
        """Return process snapshots for the current interval and clear them."""
        with self._lock:
            snapshots = self._process_snapshots
            self._process_snapshots = []
        return snapshots

    def get_network_snapshots(self) -> list:
        """Return network snapshots for the current interval and clear them."""
        with self._lock:
            snapshots = self._network_snapshots
            self._network_snapshots = []
        return snapshots

    def summarize_processes(self, snapshots: list) -> dict:
        """Summarize process activity across snapshots."""
        if not snapshots:
            return {}
        # Aggregate by process name
        from collections import Counter, defaultdict
        process_stats = defaultdict(lambda: {"count": 0, "max_cpu": 0, "max_mem": 0, "cmdlines": set()})
        for _, procs in snapshots:
            for p in procs:
                name = p["name"]
                process_stats[name]["count"] += 1
                process_stats[name]["max_cpu"] = max(process_stats[name]["max_cpu"], p["cpu_percent"])
                process_stats[name]["max_mem"] = max(process_stats[name]["max_mem"], p["memory_percent"])
                if p["cmdline"]:
                    process_stats[name]["cmdlines"].add(p["cmdline"])

        summary = []
        for name, stats in sorted(process_stats.items(), key=lambda x: -x[1]["count"]):
            summary.append({
                "process": name,
                "snapshots_seen": stats["count"],
                "max_cpu_percent": stats["max_cpu"],
                "max_memory_percent": stats["max_mem"],
                "command_lines": list(stats["cmdlines"])[:3],
            })
        return {"total_snapshots": len(snapshots), "processes": summary[:30]}

    def summarize_network(self, snapshots: list) -> dict:
        """Summarize network connections across snapshots."""
        if not snapshots:
            return {}
        from collections import Counter, defaultdict
        remote_counter = Counter()
        pid_counter = Counter()
        for _, conns in snapshots:
            for c in conns:
                remote_counter[c["remote"]] += 1
                pid_counter[c["pid"]] += 1

        return {
            "total_snapshots": len(snapshots),
            "top_remote_endpoints": [
                {"endpoint": ep, "connections": count}
                for ep, count in remote_counter.most_common(20)
            ],
            "top_pids": [
                {"pid": pid, "connections": count}
                for pid, count in pid_counter.most_common(20)
            ],
        }