"""
Evolution Metrics — Lightweight in-memory metrics collector.

No external dependencies. Counters and gauges are stored in-memory
and exported as JSON via get_metrics(). Can be upgraded to Prometheus
later by swapping the backend.
"""
import time
import threading
import logging
from typing import Dict, Any

logger = logging.getLogger("unified_core.evolution.metrics")


class EvolutionMetrics:
    """Thread-safe metrics collector for the evolution engine."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = {}
        self._start_time = time.time()

    def inc(self, name: str, value: int = 1):
        """Increment a counter."""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float):
        """Set a gauge to a specific value."""
        with self._lock:
            self._gauges[name] = value

    def observe(self, name: str, value: float, max_samples: int = 100):
        """Record a value in a histogram (keeps last N samples)."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = []
            self._histograms[name].append(value)
            # Keep only last N samples
            if len(self._histograms[name]) > max_samples:
                self._histograms[name] = self._histograms[name][-max_samples:]

    def get_metrics(self) -> Dict[str, Any]:
        """Export all metrics as a JSON-serializable dict."""
        with self._lock:
            result = {
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }
            # Add histogram summaries
            histograms = {}
            for name, values in self._histograms.items():
                if values:
                    sorted_v = sorted(values)
                    histograms[name] = {
                        "count": len(values),
                        "min": round(sorted_v[0], 2),
                        "max": round(sorted_v[-1], 2),
                        "avg": round(sum(values) / len(values), 2),
                        "p50": round(sorted_v[len(sorted_v) // 2], 2),
                        "p95": round(sorted_v[int(len(sorted_v) * 0.95)], 2) if len(sorted_v) > 1 else round(sorted_v[0], 2),
                    }
            result["histograms"] = histograms
            return result

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._start_time = time.time()


# ── Singleton ────────────────────────────────────────────────────
_instance = None
_instance_lock = threading.Lock()


def get_metrics_collector() -> EvolutionMetrics:
    """Get or create the global metrics collector."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = EvolutionMetrics()
    return _instance


# ── Convenience functions ────────────────────────────────────────

def inc(name: str, value: int = 1):
    """Increment a counter on the global collector."""
    get_metrics_collector().inc(name, value)

def set_gauge(name: str, value: float):
    """Set a gauge on the global collector."""
    get_metrics_collector().set_gauge(name, value)

def observe(name: str, value: float):
    """Record a histogram observation on the global collector."""
    get_metrics_collector().observe(name, value)

def get_metrics() -> Dict[str, Any]:
    """Export metrics from the global collector."""
    return get_metrics_collector().get_metrics()
