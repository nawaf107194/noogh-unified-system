"""
Cognitive Trace - Observability for NOOGH ReAct Loop

Phase E Implementation - GPT Verification Gate
Provides structured tracing for:
1. ReAct timeline per request
2. Iteration count and termination reason
3. Tool calls (name, args, latency, success/failure)
4. Memory recall hits with similarity scores
5. Backend used (ollama / local / degraded)
"""

import logging
import os
import time
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TraceEventType(Enum):
    """Types of trace events in the cognitive loop."""
    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"
    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MEMORY_RECALL = "memory_recall"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"
    TERMINATION = "termination"


@dataclass
class TraceEvent:
    """A single event in the cognitive trace."""
    event_type: TraceEventType
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "duration_ms": self.duration_ms
        }


@dataclass
class ToolCallTrace:
    """Trace data for a single tool call."""
    tool_name: str
    args_summary: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    result_summary: Optional[str] = None
    
    @property
    def latency_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "args": self.args_summary,
            "latency_ms": round(self.latency_ms, 2),
            "success": self.success,
            "error": self.error,
            "result": self.result_summary
        }


@dataclass
class MemoryRecallTrace:
    """Trace data for memory recall operation."""
    query: str
    num_results: int
    hits: List[Dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:100],
            "num_results": self.num_results,
            "hits": [{"id": h.get("id", "?")[:8], "similarity": round(h.get("similarity", 0), 3)} 
                     for h in self.hits[:5]],
            "latency_ms": round(self.latency_ms, 2)
        }


@dataclass
class CognitiveTrace:
    """
    Complete trace for a single cognitive request.
    This is the main observability artifact for Phase E.
    """
    trace_id: str
    request_query: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Core metrics
    iterations: int = 0
    termination_reason: str = "unknown"
    backend_used: str = "unknown"
    
    # Event timeline
    events: List[TraceEvent] = field(default_factory=list)
    
    # Aggregated data
    tool_calls: List[ToolCallTrace] = field(default_factory=list)
    memory_recalls: List[MemoryRecallTrace] = field(default_factory=list)
    
    # Final result
    final_answer: Optional[str] = None
    confidence: float = 0.0
    
    def add_event(self, event_type: TraceEventType, data: Dict[str, Any] = None, duration_ms: float = None):
        """Add an event to the trace timeline."""
        event = TraceEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            data=data or {},
            duration_ms=duration_ms
        )
        self.events.append(event)
        logger.debug(f"📊 Trace event: {event_type.value}")
    
    def start_iteration(self, iteration_num: int):
        """Mark the start of a ReAct iteration."""
        self.iterations = iteration_num + 1
        self.add_event(TraceEventType.ITERATION_START, {"iteration": iteration_num + 1})
    
    def end_iteration(self, iteration_num: int, reason: str = None):
        """Mark the end of a ReAct iteration."""
        self.add_event(TraceEventType.ITERATION_END, {
            "iteration": iteration_num + 1,
            "reason": reason
        })
    
    def add_thought(self, thought: str):
        """Record a reasoning thought."""
        self.add_event(TraceEventType.THOUGHT, {"thought": thought[:200]})
    
    def start_tool_call(self, tool_name: str, args: Dict[str, Any]) -> ToolCallTrace:
        """Start tracking a tool call."""
        args_summary = json.dumps(args, ensure_ascii=False)[:100]
        trace = ToolCallTrace(
            tool_name=tool_name,
            args_summary=args_summary,
            start_time=time.time()
        )
        self.tool_calls.append(trace)
        self.add_event(TraceEventType.TOOL_CALL, {"tool": tool_name, "args": args_summary})
        return trace
    
    def end_tool_call(self, trace: ToolCallTrace, success: bool, result: str = None, error: str = None):
        """Complete tracking a tool call."""
        trace.end_time = time.time()
        trace.success = success
        trace.result_summary = result[:200] if result else None
        trace.error = error
        self.add_event(TraceEventType.TOOL_RESULT, trace.to_dict(), trace.latency_ms)
    
    def add_memory_recall(self, query: str, results: List[Dict[str, Any]], latency_ms: float):
        """Record a memory recall operation."""
        recall_trace = MemoryRecallTrace(
            query=query,
            num_results=len(results),
            hits=results,
            latency_ms=latency_ms
        )
        self.memory_recalls.append(recall_trace)
        self.add_event(TraceEventType.MEMORY_RECALL, recall_trace.to_dict(), latency_ms)
    
    def set_termination(self, reason: str, final_answer: str, confidence: float):
        """Record the final termination of the request."""
        self.end_time = time.time()
        self.termination_reason = reason
        self.final_answer = final_answer
        self.confidence = confidence
        self.add_event(TraceEventType.TERMINATION, {
            "reason": reason,
            "confidence": round(confidence, 3)
        })
    
    def set_backend(self, backend: str):
        """Record which backend is being used."""
        self.backend_used = backend
        self.add_event(TraceEventType.REQUEST_START, {"backend": backend})
    
    @property
    def total_duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    @property
    def total_tool_calls(self) -> int:
        return len(self.tool_calls)
    
    @property
    def successful_tool_calls(self) -> int:
        return sum(1 for t in self.tool_calls if t.success)
    
    @property
    def reasoning_trace(self) -> List[str]:
        """Convert events to a simple list of strings for legacy support."""
        return [f"{e.event_type.value}: {json.dumps(e.data, ensure_ascii=False)[:100]}" for e in self.events]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export the full trace as a dictionary."""
        return {
            "trace_id": self.trace_id,
            "query": self.request_query[:100],
            "summary": {
                "total_duration_ms": round(self.total_duration_ms, 2),
                "iterations": self.iterations,
                "termination_reason": self.termination_reason,
                "backend": self.backend_used,
                "tool_calls": f"{self.successful_tool_calls}/{self.total_tool_calls}",
                "memory_recalls": len(self.memory_recalls),
                "confidence": round(self.confidence, 3)
            },
            "timeline": [e.to_dict() for e in self.events],
            "tool_details": [t.to_dict() for t in self.tool_calls],
            "memory_details": [m.to_dict() for m in self.memory_recalls]
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Export as formatted JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    def summary_line(self) -> str:
        """One-line summary for logging."""
        return (
            f"[{self.trace_id[:8]}] "
            f"{self.iterations} iters | "
            f"{self.successful_tool_calls}/{self.total_tool_calls} tools | "
            f"{len(self.memory_recalls)} recalls | "
            f"{self.termination_reason} | "
            f"{round(self.total_duration_ms)}ms | "
            f"conf={round(self.confidence, 2)}"
        )


# ============================================================================
# TRACE MANAGER - Global trace collection
# ============================================================================

class TraceManager:
    """
    Manages cognitive traces for the NOOGH system.
    Provides storage, retrieval, and dashboard data.
    """
    
    MAX_TRACES = 100  # Keep last N traces in memory
    LOG_FILE = "/home/noogh/projects/noogh_unified_system/data/logs/forensics_trace.jsonl"
    
    def __init__(self):
        self.traces: List[CognitiveTrace] = []
        self._trace_counter = 0
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

    def log_persistent(self, trace: CognitiveTrace):
        """Append trace to permanent JSONL storage (v12.8 Trust)."""
        try:
            # Ensure folder exists
            log_dir = os.path.dirname(self.LOG_FILE)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to log cognitive trace to {self.LOG_FILE}: {e}")
    
    def create_trace(self, query: str) -> CognitiveTrace:
        """Create a new trace for a request."""
        self._trace_counter += 1
        trace_id = f"trace_{self._trace_counter}_{int(time.time())}"
        trace = CognitiveTrace(trace_id=trace_id, request_query=query)
        self.traces.append(trace)
        
        # Trim old memory traces
        if len(self.traces) > self.MAX_TRACES:
            self.traces = self.traces[-self.MAX_TRACES:]
        
        logger.info(f"📊 New trace created: {trace_id}")
        return trace

    # NOTE: Duplicate log_persistent removed (HIGH-03 fix). Using definition at L279.
    
    def get_trace(self, trace_id: str) -> Optional[CognitiveTrace]:
        """Get a specific trace by ID."""
        for trace in self.traces:
            if trace.trace_id == trace_id:
                return trace
        return None
    
    def get_recent_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent traces for dashboard display."""
        recent = self.traces[-limit:]
        return [t.to_dict() for t in reversed(recent)]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get aggregated data for the cognitive dashboard."""
        if not self.traces:
            return {
                "total_requests": 0,
                "avg_duration_ms": 0,
                "avg_iterations": 0,
                "tool_success_rate": 0,
                "recent_traces": []
            }
        
        total_duration = sum(t.total_duration_ms for t in self.traces)
        total_iterations = sum(t.iterations for t in self.traces)
        total_tools = sum(t.total_tool_calls for t in self.traces)
        successful_tools = sum(t.successful_tool_calls for t in self.traces)
        
        return {
            "total_requests": len(self.traces),
            "avg_duration_ms": round(total_duration / len(self.traces), 2),
            "avg_iterations": round(total_iterations / len(self.traces), 2),
            "tool_success_rate": round(successful_tools / total_tools * 100, 1) if total_tools > 0 else 0,
            "backends_used": list(set(t.backend_used for t in self.traces)),
            "recent_traces": self.get_recent_traces(5)
        }


# Singleton instance
_trace_manager: Optional[TraceManager] = None

def get_trace_manager() -> TraceManager:
    """Get or create the global trace manager."""
    global _trace_manager
    if _trace_manager is None:
        _trace_manager = TraceManager()
        logger.info("📊 TraceManager initialized")
    return _trace_manager


def reset_trace_manager():
    """Reset the trace manager (for testing)."""
    global _trace_manager
    _trace_manager = None
