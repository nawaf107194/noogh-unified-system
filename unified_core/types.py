"""
Unified Core Types - Central type definitions.

All shared types should be defined here to avoid duplicate definitions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time


@dataclass
class ToolCall:
    """A tool call request from the agent."""
    tool_name: str
    arguments: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "timestamp": self.timestamp
        }


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms
        }


__all__ = ["ToolCall", "ToolResult"]
