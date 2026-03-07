"""
Metrics Collector - Historical System Metrics Storage
Version: 1.0.0

Collects and stores system metrics over time for time series prediction.
Runs continuously in the background.
"""

import logging
import os
import time
import json
import sqlite3
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio

logger = logging.getLogger("unified_core.ml.metrics_collector")

# Lazy import for psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - MetricsCollector disabled")


@dataclass
class SystemMetrics:
    """System metrics at a point in time."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    gpu_percent: float = 0.0
    gpu_temp: float = 0.0
    gpu_memory_used: float = 0.0
    gpu_memory_total: float = 0.0

    # Additional context
    active_processes: int = 0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0


class MetricsCollector:
    """
    Collects system metrics continuously and stores them for training.

    Storage: SQLite database for efficient time-series queries
    Frequency: Configurable (default: every 10 seconds)
    Retention: Configurable (default: 7 days)
    """

    def __init__(self, db_path: str = "data/metrics/system_metrics.db",
                 collection_interval: int = 10,
                 retention_days: int = 7):
        """
        Args:
            db_path: Path to SQLite database
            collection_interval: Seconds between collections
            retention_days: Days to keep historical data
        """
        self.db_path = db_path
        self.collection_interval = collection_interval
        self.retention_days = retention_days
        self._running = False

        # Create directory
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.info(
            f"MetricsCollector initialized | "
            f"interval={collection_interval}s, retention={retention_days}d"
        )

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                cpu_percent REAL NOT NULL,
                memory_percent REAL NOT NULL,
                disk_percent REAL NOT NULL,
                gpu_percent REAL DEFAULT 0,
                gpu_temp REAL DEFAULT 0,
                gpu_memory_used REAL DEFAULT 0,
                gpu_memory_total REAL DEFAULT 0,
                active_processes INTEGER DEFAULT 0,
                network_bytes_sent INTEGER DEFAULT 0,
                network_bytes_recv INTEGER DEFAULT 0
            )
        """)

        # Create index on timestamp for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON metrics(timestamp)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Database initialized: {self.db_path}")

    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        if not PSUTIL_AVAILABLE:
            raise RuntimeError("psutil not available")

        timestamp = time.time()

        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Network
        net_io = psutil.net_io_counters()

        # Process count
        active_processes = len(psutil.pids())

        # GPU (if available)
        gpu_percent = 0.0
        gpu_temp = 0.0
        gpu_memory_used = 0.0
        gpu_memory_total = 0.0

        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                values = result.stdout.strip().split(',')
                gpu_percent = float(values[0].strip())
                gpu_temp = float(values[1].strip())
                gpu_memory_used = float(values[2].strip())
                gpu_memory_total = float(values[3].strip())
        except Exception as e:
            logger.debug(f"GPU metrics not available: {e}")

        metrics = SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            gpu_percent=gpu_percent,
            gpu_temp=gpu_temp,
            gpu_memory_used=gpu_memory_used,
            gpu_memory_total=gpu_memory_total,
            active_processes=active_processes,
            network_bytes_sent=net_io.bytes_sent,
            network_bytes_recv=net_io.bytes_recv
        )

        logger.debug(
            f"Metrics collected: CPU={cpu_percent:.1f}%, "
            f"RAM={memory.percent:.1f}%, GPU={gpu_percent:.1f}%"
        )

        return metrics

    def store_metrics(self, metrics: SystemMetrics):
        """Store metrics in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO metrics (
                timestamp, cpu_percent, memory_percent, disk_percent,
                gpu_percent, gpu_temp, gpu_memory_used, gpu_memory_total,
                active_processes, network_bytes_sent, network_bytes_recv
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
            metrics.disk_percent, metrics.gpu_percent, metrics.gpu_temp,
            metrics.gpu_memory_used, metrics.gpu_memory_total,
            metrics.active_processes, metrics.network_bytes_sent,
            metrics.network_bytes_recv
        ))

        conn.commit()
        conn.close()

    def get_recent_metrics(self, hours: int = 24, limit: Optional[int] = None) -> List[SystemMetrics]:
        """
        Get recent metrics from database.

        Args:
            hours: Hours of history to retrieve
            limit: Maximum number of records (None = all)

        Returns:
            List of SystemMetrics ordered by timestamp (oldest first)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = time.time() - (hours * 3600)

        query = """
            SELECT timestamp, cpu_percent, memory_percent, disk_percent,
                   gpu_percent, gpu_temp, gpu_memory_used, gpu_memory_total,
                   active_processes, network_bytes_sent, network_bytes_recv
            FROM metrics
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (cutoff_time,))
        rows = cursor.fetchall()
        conn.close()

        metrics = [
            SystemMetrics(
                timestamp=row[0], cpu_percent=row[1], memory_percent=row[2],
                disk_percent=row[3], gpu_percent=row[4], gpu_temp=row[5],
                gpu_memory_used=row[6], gpu_memory_total=row[7],
                active_processes=row[8], network_bytes_sent=row[9],
                network_bytes_recv=row[10]
            )
            for row in rows
        ]

        logger.info(f"Retrieved {len(metrics)} metrics from last {hours}h")

        return metrics

    def cleanup_old_data(self):
        """Remove data older than retention_days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = time.time() - (self.retention_days * 86400)

        cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_time,))
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old metrics records")

    def get_stats(self) -> Dict:
        """Get collection statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM metrics")
        count, min_ts, max_ts = cursor.fetchone()

        conn.close()

        if count > 0:
            duration_hours = (max_ts - min_ts) / 3600
        else:
            duration_hours = 0

        return {
            "total_records": count,
            "duration_hours": round(duration_hours, 2),
            "oldest_timestamp": min_ts,
            "newest_timestamp": max_ts
        }

    async def run_forever(self):
        """Run collection loop forever."""
        if not PSUTIL_AVAILABLE:
            raise RuntimeError("psutil not available")

        self._running = True
        logger.info(f"Starting metrics collection (every {self.collection_interval}s)")

        cleanup_counter = 0

        while self._running:
            try:
                # Collect and store
                metrics = self.collect_metrics()
                self.store_metrics(metrics)

                # Cleanup every ~1000 collections
                cleanup_counter += 1
                if cleanup_counter >= 1000:
                    self.cleanup_old_data()
                    cleanup_counter = 0

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

            # Wait for next collection
            await asyncio.sleep(self.collection_interval)

    def stop(self):
        """Stop collection loop."""
        self._running = False
        logger.info("Stopping metrics collection")


# Singleton instance
_collector_instance: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get singleton MetricsCollector instance."""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = MetricsCollector()
    return _collector_instance


# Standalone runner
async def main():
    """Run metrics collector standalone."""
    import argparse
    parser = argparse.ArgumentParser(description="NOOGH Metrics Collector")
    parser.add_argument('--interval', type=int, default=10,
                        help='Collection interval in seconds (default: 10)')
    parser.add_argument('--retention', type=int, default=7,
                        help='Data retention in days (default: 7)')
    args = parser.parse_args()

    collector = MetricsCollector(
        collection_interval=args.interval,
        retention_days=args.retention
    )

    try:
        await collector.run_forever()
    except KeyboardInterrupt:
        collector.stop()
        logger.info("Metrics collector stopped")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    asyncio.run(main())
