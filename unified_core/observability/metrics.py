"""
NOOGH Observability - Metrics

Prometheus-compatible metrics collection.

Key Metrics:
- Message Bus: queue depth, DLQ, latency
- Tasks: execution time, failures, blocks
- Tools: execution time by tool and isolation
- Security: blocked actions by reason
"""

from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime
import threading


class MetricsCollector:
    """
    Prometheus-compatible metrics collector.
    
    Thread-safe metrics storage for:
    - Counters (monotonically increasing)
    - Gauges (can go up or down)
    - Histograms (distribution of values)
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # Counters
        self._counters: Dict[str, float] = defaultdict(float)
        
        # Gauges
        self._gauges: Dict[str, float] = defaultdict(float)
        
        # Histograms (store all values for now, optimize later)
        self._histograms: Dict[str, list] = defaultdict(list)
    
    # ==================================================================
    # Counters (always increase)
    # ==================================================================
    
    def inc_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0):
        """
        Increment counter.
        
        Args:
            name: Metric name
            labels: Optional labels dictionary
            value: Increment amount (default 1.0)
        """
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0.0)
    
    # ==================================================================
    # Gauges (can increase or decrease)
    # ==================================================================
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge to specific value"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def inc_gauge(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = self._gauges.get(key, 0.0) + value
    
    def dec_gauge(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge"""
        self.inc_gauge(name, -value, labels)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, labels)
        with self._lock:
            return self._gauges.get(key, 0.0)
    
    # ==================================================================
    # Histograms (track distributions)
    # ==================================================================
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Observe value for histogram.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels
        """
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            
            # Keep only last 10000 values to prevent memory growth
            if len(self._histograms[key]) > 10000:
                self._histograms[key] = self._histograms[key][-10000:]
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Get histogram statistics.
        
        Returns:
            Dict with count, sum, p50, p95, p99
        """
        key = self._make_key(name, labels)
        with self._lock:
            values = self._histograms.get(key, [])
            
            if not values:
                return {
                    "count": 0,
                    "sum": 0.0,
                    "p50": 0.0,
                    "p95": 0.0,
                    "p99": 0.0
                }
            
            sorted_values = sorted(values)
            count = len(sorted_values)
            
            return {
                "count": count,
                "sum": sum(sorted_values),
                "p50": sorted_values[int(count * 0.50)],
                "p95": sorted_values[int(count * 0.95)],
                "p99": sorted_values[int(count * 0.99)]
            }
    
    # ==================================================================
    # Prometheus Export
    # ==================================================================
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        # Counters
        for key, value in self._counters.items():
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self._gauges.items():
            lines.append(f"{key} {value}")
        
        # Histograms
        for key, values in self._histograms.items():
            if values:
                stats = self.get_histogram_stats(key.split("{")[0] if "{" in key else key)
                lines.append(f"{key}_count {stats['count']}")
                lines.append(f"{key}_sum {stats['sum']}")
                lines.append(f"{key}{{quantile=\"0.5\"}} {stats['p50']}")
                lines.append(f"{key}{{quantile=\"0.95\"}} {stats['p95']}")
                lines.append(f"{key}{{quantile=\"0.99\"}} {stats['p99']}")
        
        return "\n".join(lines)
    
    # ==================================================================
    # Helpers
    # ==================================================================
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# ==================================================================
# Global Singleton
# ==================================================================

_metrics_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get global metrics collector singleton"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# ==================================================================
# Convenience Functions
# ==================================================================

def inc_counter(name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0):
    """Increment counter (convenience function)"""
    get_metrics().inc_counter(name, labels, value)


def set_gauge(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Set gauge (convenience function)"""
    get_metrics().set_gauge(name, value, labels)


def observe_histogram(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Observe histogram value (convenience function)"""
    get_metrics().observe_histogram(name, value, labels)


# Example usage
if __name__ == "__main__":
    metrics = get_metrics()
    
    # Counter
    inc_counter("requests_total", {"endpoint": "/query", "status": "200"})
    inc_counter("requests_total", {"endpoint": "/query", "status": "200"})
    
    # Gauge
    set_gauge("active_tasks", 5)
    
    # Histogram
    observe_histogram("task_latency_ms", 150.5, {"agent": "code_executor"})
    observe_histogram("task_latency_ms", 200.3, {"agent": "code_executor"})
    
    # Export
    print(metrics.export_prometheus())
