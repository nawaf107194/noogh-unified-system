"""
NOOGH Observability - Structured Logging

Production-grade JSON logging with trace IDs.

CRITICAL:
- All logs are JSON formatted
- Every log includes trace_id for request tracking
- Service name included for multi-service deployments
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar

# Context variable for trace ID
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


class StructuredLogger:
    """
    Structured JSON logger for production observability.
    
    Every log entry includes:
    - timestamp (ISO 8601)
    - service (service name)
    - trace_id (request tracking)
    - level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    - message
    - extra fields (optional)
    """
    
    def __init__(self, service_name: str, level: int = logging.INFO):
        """
        Initialize structured logger.
        
        Args:
            service_name: Name of the service (gateway, orchestrator, agent, etc.)
            level: Logging level
        """
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(level)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter(service_name))
        self.logger.addHandler(handler)
    
    def _log(self, level: int, message: str, **extra):
        """Internal log method"""
        trace_id = trace_id_var.get()
        
        # Add trace_id to extra
        if trace_id:
            extra['trace_id'] = trace_id
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **extra):
        """Debug level log"""
        self._log(logging.DEBUG, message, **extra)
    
    def info(self, message: str, **extra):
        """Info level log"""
        self._log(logging.INFO, message, **extra)
    
    def warning(self, message: str, **extra):
        """Warning level log"""
        self._log(logging.WARNING, message, **extra)
    
    def error(self, message: str, **extra):
        """Error level log"""
        self._log(logging.ERROR, message, **extra)
    
    def critical(self, message: str, **extra):
        """Critical level log"""
        self._log(logging.CRITICAL, message, **extra)


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Output format:
    {
        "timestamp": "2026-01-21T17:18:00.000Z",
        "service": "gateway",
        "level": "INFO",
        "message": "Request received",
        "trace_id": "trace-001",
        "user_id": "user-123",
        ...
    }
    """
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add trace_id if available
        if hasattr(record, 'trace_id'):
            log_data['trace_id'] = record.trace_id
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def set_trace_id(trace_id: str):
    """
    Set trace ID for current context.
    
    This trace ID will be included in all logs within this context.
    
    Args:
        trace_id: Unique trace identifier
    """
    trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    return trace_id_var.get()


def clear_trace_id():
    """Clear trace ID from current context"""
    trace_id_var.set(None)


# Convenience function to get logger
def get_logger(service_name: str, level: int = logging.INFO) -> StructuredLogger:
    """
    Get structured logger for a service.
    
    Args:
        service_name: Name of the service
        level: Logging level
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(service_name, level)


# Example usage:
if __name__ == "__main__":
    # Create logger
    logger = get_logger("test-service")
    
    # Set trace ID
    set_trace_id("trace-test-001")
    
    # Log with trace
    logger.info("Test message", user_id="user-123", action="test")
    logger.warning("Test warning", error_code="WARN_001")
    
    # Log without trace
    clear_trace_id()
    logger.info("Message without trace")
