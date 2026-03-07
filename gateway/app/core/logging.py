import json
import logging
import sys
from typing import Any, Dict

from gateway.app.core.config import get_settings

settings = get_settings()

import contextvars
from typing import Any, Dict

# Global context for structured logging - ASYNC SAFE
_log_context_var = contextvars.ContextVar("log_context", default={})

def get_log_context() -> Dict[str, Any]:
    return _log_context_var.get()

def set_log_context(**kwargs):
    """Update log context for the current async task/thread"""
    ctx = _log_context_var.get().copy()
    ctx.update(kwargs)
    _log_context_var.set(ctx)

class JsonFormatter(logging.Formatter):
    """Custom formatter to output logs in JSON format"""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }
        
        # Add context from ContextVar (Async Safe)
        ctx = get_log_context()
        log_record.update(ctx)
        
        # Ensure trace_id is top-level if present in context (aliased from request_id)
        if "request_id" in ctx:
            log_record["trace_id"] = ctx["request_id"]

        # Add extra fields if provided
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)

        return json.dumps(log_record)


def setup_logging():
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logging.basicConfig(level=level, handlers=[handler], force=True)  # Override any existing config

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str):
    return logging.getLogger(name)
