"""
Real Metrics Collector
Replaces simulated metrics with actual system performance tracking.
Stores metrics in-memory and persists interactions to disk for analysis.
"""

import json
import statistics
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class MetricsCollector:
    """
    Collects REAL performance metrics from the running application.
    """

    def __init__(self):
        # Rolling window of last 1000 request latencies
        self.latencies: deque = deque(maxlen=1000)

        # Counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = time.time()

        # Interaction logging
        self.logs_dir = Path("./logs/interactions")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.current_log_file = self.logs_dir / f"interactions_{datetime.now().strftime('%Y%m%d')}.jsonl"

        # Failure tracking for Auto-Curriculum
        self.failure_counts: Dict[str, int] = {}
        self.topic_counts: Dict[str, int] = {}

    def record_request(self, method: str, path: str, duration_sec: float, status_code: int):
        """Record a completed request"""
        self.total_requests += 1
        self.latencies.append(duration_sec * 1000)  # Convert to ms

        if 200 <= status_code < 400:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def log_interaction(self, query: str, response: str, success: bool, metadata: Dict = None):
        """
        Log user interaction details to file for Auto-Curriculum analysis.
        This provides generic 'Ground Truth' for learning.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "success": success,
            "metadata": metadata or {},
        }

        # Asynchronously write to file to avoid blocking
        # For simplicity in this sync context, we append directly
        # In high load, this should be buffered
        with open(self.current_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        # Update in-memory stats for immediate analysis
        self._update_topic_stats(query)
        if not success:
            self._update_failure_stats(query)

    def _update_topic_stats(self, query: str):
        """Simple keyword-based topic classification (Real, not simulated)"""
        query_lower = query.lower()
        if "code" in query_lower or "python" in query_lower or "function" in query_lower:
            self.topic_counts["code_generation"] = self.topic_counts.get("code_generation", 0) + 1
        elif "debug" in query_lower or "error" in query_lower or "fix" in query_lower:
            self.topic_counts["debugging"] = self.topic_counts.get("debugging", 0) + 1
        elif "audit" in query_lower or "explain" in query_lower:
            self.topic_counts["analysis"] = self.topic_counts.get("analysis", 0) + 1
        # Add simpler language detection
        if any("\u0600" <= c <= "\u06ff" for c in query):  # Arabic range
            self.topic_counts["arabic"] = self.topic_counts.get("arabic", 0) + 1

    def _update_failure_stats(self, query: str):
        """Categorize failures"""
        query_lower = query.lower()
        if "math" in query_lower:
            self.failure_counts["math"] = self.failure_counts.get("math", 0) + 1
        elif len(query) > 500:
            self.failure_counts["complexity"] = self.failure_counts.get("complexity", 0) + 1

    def reset_counters(self):
        """Reset all counters to clear stale metrics"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.latencies.clear()
        self.failure_counts.clear()
        self.topic_counts.clear()

    def get_performance_snapshot(self) -> Dict[str, Any]:
        """Get real performance metrics"""
        uptime = time.time() - self.start_time
        req_per_sec = self.total_requests / uptime if uptime > 0 else 0

        if not self.latencies:
            return {
                "avg_response_time_ms": 0.0,
                "requests_per_second": round(req_per_sec, 2),
                "success_rate": 1.0,
                "error_rate": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
            }

        lat_list = sorted(list(self.latencies))
        avg_lat = statistics.mean(lat_list)
        success_rate = self.successful_requests / self.total_requests if self.total_requests > 0 else 1.0

        return {
            "avg_response_time_ms": round(avg_lat, 2),
            "requests_per_second": round(req_per_sec, 2),
            "success_rate": round(success_rate, 4),
            "error_rate": round(1.0 - success_rate, 4),
            "p50_latency_ms": round(lat_list[int(len(lat_list) * 0.5)], 2),
            "p95_latency_ms": round(lat_list[int(len(lat_list) * 0.95)], 2),
            "p99_latency_ms": round(lat_list[int(len(lat_list) * 0.99)], 2),
        }


# Singleton instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
