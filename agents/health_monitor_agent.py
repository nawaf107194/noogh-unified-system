#!/usr/bin/env python3
"""
NOOGH Health Monitor Agent - FIXED v2
Monitors system health: CPU, RAM, disk, services, logs.
Uses only stdlib - reads /proc for metrics, no psutil needed.
"""
import sys
import os
import re
import json
import time
import logging
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | health_monitor | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/noogh/projects/noogh_unified_system/src/logs/health_monitor.log"),
    ],
)
logger = logging.getLogger("agents.health_monitor")

SRC = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"


def _get_cpu_percent() -> float:
    """Read CPU usage from /proc/stat (two-sample delta)."""
    def _read_stat():
        with open("/proc/stat") as f:
            line = f.readline()
        vals = list(map(int, line.split()[1:]))
        total = sum(vals)
        idle = vals[3]
        return total, idle
    try:
        t1, i1 = _read_stat()
        time.sleep(0.3)
        t2, i2 = _read_stat()
        dt = t2 - t1
        di = i2 - i1
        return round((1 - di / dt) * 100, 1) if dt > 0 else 0.0
    except Exception:
        return 0.0


def _get_mem_percent() -> Dict[str, Any]:
    """Read memory info from /proc/meminfo."""
    try:
        with open("/proc/meminfo") as f:
            content = f.read()
        total = int(re.search(r"MemTotal:\s+(\d+)", content).group(1))
        avail = int(re.search(r"MemAvailable:\s+(\d+)", content).group(1))
        used = total - avail
        return {
            "total_gb": round(total / 1024 / 1024, 2),
            "used_gb": round(used / 1024 / 1024, 2),
            "percent": round(used / total * 100, 1),
        }
    except Exception as e:
        return {"total_gb": 0, "used_gb": 0, "percent": 0, "error": str(e)}


def _get_disk_percent(path: str = "/") -> Dict[str, Any]:
    """Get disk usage using os.statvfs."""
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bfree * st.f_frsize
        used = total - free
        return {
            "total_gb": round(total / 1e9, 1),
            "used_gb": round(used / 1e9, 1),
            "percent": round(used / total * 100, 1) if total > 0 else 0,
        }
    except Exception as e:
        return {"total_gb": 0, "used_gb": 0, "percent": 0, "error": str(e)}


def _get_load_avg() -> List[float]:
    """Read load averages from /proc/loadavg."""
    try:
        with open("/proc/loadavg") as f:
            parts = f.read().split()
        return [float(parts[0]), float(parts[1]), float(parts[2])]
    except Exception:
        return [0.0, 0.0, 0.0]


def _check_services() -> Dict[str, str]:
    """Check systemd service statuses."""
    services = ["noogh-agent", "noogh-neural", "noogh-gateway"]
    result = {}
    for svc in services:
        try:
            r = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True, timeout=5
            )
            result[svc] = r.stdout.strip()
        except Exception:
            result[svc] = "unknown"
    return result


def _scan_recent_errors(max_lines: int = 50) -> List[str]:
    """Scan recent log files for ERROR lines."""
    errors = []
    log_dir = Path(f"{SRC}/logs")
    if not log_dir.exists():
        return errors
    for log_file in log_dir.glob("*.log"):
        try:
            lines = log_file.read_text(errors="ignore").split("\n")
            for line in lines[-max_lines:]:
                if "ERROR" in line or "CRITICAL" in line:
                    errors.append(f"[{log_file.name}] {line.strip()[:120]}")
        except Exception:
            pass
    return errors[-10:]  # Return last 10 errors max


def _db_inject(key: str, data: Any):
    """Write metric to shared memory DB."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.execute(
            "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) VALUES (?, ?, ?, ?)",
            (key, json.dumps(data, default=str), 0.95, time.time())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"DB inject failed: {e}")


def collect_metrics() -> Dict[str, Any]:
    """Collect all system metrics and return a snapshot."""
    cpu = _get_cpu_percent()
    mem = _get_mem_percent()
    disk = _get_disk_percent("/")
    load = _get_load_avg()
    services = _check_services()
    errors = _scan_recent_errors()

    alerts = []
    if cpu > 90:
        alerts.append(f"CPU critical: {cpu}%")
    if mem["percent"] > 85:
        alerts.append(f"RAM high: {mem['percent']}%")
    if disk["percent"] > 90:
        alerts.append(f"Disk critical: {disk['percent']}%")
    for svc, state in services.items():
        if state not in ("active", "unknown"):
            alerts.append(f"Service {svc} is {state}")
    if errors:
        alerts.append(f"{len(errors)} recent ERROR lines found")

    status = "healthy"
    if len(alerts) >= 3 or cpu > 95 or mem["percent"] > 95:
        status = "critical"
    elif alerts:
        status = "warning"

    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": status,
        "cpu_percent": cpu,
        "memory": mem,
        "disk": disk,
        "load_avg": load,
        "services": services,
        "alerts": alerts,
        "recent_errors": errors[:5],
    }
    return snapshot


class HealthMonitorAgent:
    """
    NOOGH Health Monitor Agent.
    Collects system metrics and stores them in shared memory DB.
    Compatible with the orchestrator's --report interface.
    """

    def __init__(self):
        logger.info("✅ HealthMonitorAgent initialized")

    def run_once(self) -> Dict[str, Any]:
        """Run a single health check and store results."""
        logger.info("Running health check...")
        snapshot = collect_metrics()

        # Store in shared memory
        _db_inject("health:snapshot", snapshot)

        # Log summary
        logger.info(
            f"Status={snapshot['status']} | "
            f"CPU={snapshot['cpu_percent']}% | "
            f"RAM={snapshot['memory']['percent']}% | "
            f"Disk={snapshot['disk']['percent']}% | "
            f"Load={snapshot['load_avg'][0]}"
        )

        if snapshot["alerts"]:
            for alert in snapshot["alerts"]:
                logger.warning(f"  ⚠️ {alert}")
        else:
            logger.info("  All systems normal.")

        return snapshot

    def run_loop(self, interval: int = 300):
        """Run health checks in a loop every `interval` seconds."""
        logger.info(f"Starting health monitor loop (every {interval}s)")
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Health check error: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser(description="NOOGH Health Monitor")
    p.add_argument("--report", action="store_true", help="Print JSON report and exit")
    p.add_argument("--loop", action="store_true", help="Run in loop")
    p.add_argument("--interval", type=int, default=300, help="Loop interval in seconds")
    args = p.parse_args()

    agent = HealthMonitorAgent()

    if args.loop:
        agent.run_loop(args.interval)
    else:
        result = agent.run_once()
        print(json.dumps(result, indent=2, default=str))
