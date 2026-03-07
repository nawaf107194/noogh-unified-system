"""
NOOGH Observability Package

Production observability infrastructure.
"""

from unified_core.observability.logger import (
    get_logger,
    set_trace_id,
    get_trace_id,
    clear_trace_id,
    StructuredLogger
)

from unified_core.observability.metrics import (
    get_metrics,
    inc_counter,
    set_gauge,
    observe_histogram,
    MetricsCollector
)

__all__ = [
    # Logging
    "get_logger",
    "set_trace_id",
    "get_trace_id",
    "clear_trace_id",
    "StructuredLogger",
    
    # Metrics
    "get_metrics",
    "inc_counter",
    "set_gauge",
    "observe_histogram",
    "MetricsCollector"
]
