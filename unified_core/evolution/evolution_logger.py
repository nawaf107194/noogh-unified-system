"""
Evolution Logger — Unified logging with request ID injection.

Provides a logging filter that automatically adds request_id and component
fields to all log records in the evolution module hierarchy.
"""
import logging
import threading
import uuid
from typing import Optional


# Thread-local storage for request context
_context = threading.local()


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set a request ID for the current thread. Returns the ID."""
    rid = request_id or uuid.uuid4().hex[:12]
    _context.request_id = rid
    return rid


def get_request_id() -> str:
    """Get the current request ID, or 'no-req' if none set."""
    return getattr(_context, 'request_id', None) or 'no-req'


def clear_request_id():
    """Clear the current request ID."""
    _context.request_id = None


class RequestIdFilter(logging.Filter):
    """Injects request_id and component into every log record."""

    def __init__(self, component: str = "evolution"):
        super().__init__()
        self.component = component

    def filter(self, record):
        record.request_id = get_request_id()
        record.component = self.component
        return True


# Pre-built format string for evolution loggers
EVOLUTION_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-7s | %(component)s | "
    "req=%(request_id)s | %(name)s | %(message)s"
)


def setup_evolution_logging(level: int = logging.INFO):
    """Configure all evolution loggers with request ID injection.

    Call once at startup. Adds RequestIdFilter to the evolution
    logger hierarchy and sets a unified format.
    """
    # Root evolution logger
    evo_logger = logging.getLogger("unified_core.evolution")
    evo_logger.setLevel(level)

    # Add filter to existing handlers, or create a stream handler
    if not evo_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(EVOLUTION_LOG_FORMAT))
        handler.addFilter(RequestIdFilter("evolution"))
        evo_logger.addHandler(handler)
    else:
        for handler in evo_logger.handlers:
            # Add filter if not already present
            if not any(isinstance(f, RequestIdFilter) for f in handler.filters):
                handler.addFilter(RequestIdFilter("evolution"))

    # Neural bridge logger
    nb_logger = logging.getLogger("unified_core.neural_bridge")
    if not any(isinstance(f, RequestIdFilter) for f in nb_logger.filters):
        nb_logger.addFilter(RequestIdFilter("neural_bridge"))

    return evo_logger
