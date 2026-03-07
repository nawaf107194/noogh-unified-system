"""
Gateway app package initializer.

Expose common subpackages used during test collection (notably `llm`).
This file is intentionally minimal to avoid importing heavy ML deps at package import time.
"""

__all__ = ["llm"]

try:
    # Import the `llm` subpackage if available so attribute access like
    # `gateway.app.llm` works during test collection and runtime.
    from . import llm  # type: ignore
except Exception:
    llm = None
