"""
Shared Pydantic models for noogh_unified_system.

Single source of truth for request/response models used across
neural_engine and gateway services.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# --- Process Models ---

class ProcessRequest(BaseModel):
    """Request model for neural processing."""
    text: str
    context: Optional[Dict[str, Any]] = None
    store_memory: bool = True
    pre_fill: Optional[str] = None


class ProcessResponse(BaseModel):
    """Response model for neural processing."""
    conclusion: str
    confidence: float
    reasoning_trace: List[str]
    suggested_actions: List[str]
    memories_recalled: Optional[List[Dict[str, Any]]] = None
    raw_response: Optional[str] = None


# --- Memory Models ---

class MemoryRequest(BaseModel):
    """Request to store a memory."""
    content: str
    metadata: Optional[Dict[str, Any]] = None


class MemoryResponse(BaseModel):
    """Response after storing a memory."""
    id: str
    content: str
    timestamp: str


class RecallRequest(BaseModel):
    """Request to recall memories."""
    query: str
    n_results: int = 5


class RecallResponse(BaseModel):
    """Response from memory recall."""
    memories: List[Dict[str, Any]]
    count: int


# --- ReAct Models ---

class ReActRequest(BaseModel):
    """Request for ReAct-enabled processing."""
    text: str
    context: Optional[Dict[str, Any]] = None
    store_memory: bool = True
    use_react: bool = True
    password: Optional[str] = None


class ReActResponse(BaseModel):
    """Response from ReAct processing."""
    answer: str
    confidence: float
    iterations: int
    tool_calls: List[Dict[str, Any]]
    observations: List[str]
    reasoning_trace: List[str]
    memories_recalled: Optional[List[Dict[str, Any]]] = None


# --- Vision Models ---

class VisionRequest(BaseModel):
    """Request for vision processing."""
    image_path: str
    query: Optional[str] = None


# --- Dream Models ---

class DreamRequest(BaseModel):
    """Request to trigger dream cycle."""
    duration_minutes: int = 5
