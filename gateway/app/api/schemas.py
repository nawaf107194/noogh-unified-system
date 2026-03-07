from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Enums
class ServiceStatus(str, Enum):
    online = "online"
    offline = "offline"
    degraded = "degraded"

class AgentStatus(str, Enum):
    online = "online"
    offline = "offline"
    busy = "busy"

class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    blocked = "blocked"

class IsolationTier(str, Enum):
    none = "none"
    sandbox = "sandbox"
    lab_container = "lab_container"

# System Schemas
class ServiceInfo(BaseModel):
    name: str
    status: ServiceStatus
    port: Optional[int] = None
    metrics_port: Optional[int] = None
    uptime_seconds: Optional[float] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)

class SystemMetrics(BaseModel):
    active_tasks: int = 0
    agents_online: int = 0
    tools_executed_1h: int = 0
    blocked_actions_1h: int = 0
    sandbox_executions_1h: int = 0
    lab_executions_1h: int = 0
    avg_execution_ms: float = 0.0
    # Security Metrics
    amla_status: str = "unknown"
    validator_status: str = "unknown"
    governance_status: str = "unknown"
    budget_enforcement: str = "unknown"
    security_score: float = 0.0

class SystemStatus(BaseModel):
    services: List[ServiceInfo]
    metrics: SystemMetrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Agent Schemas
class AgentInfo(BaseModel):
    agent_id: str
    role: str
    capabilities: List[str]
    status: AgentStatus
    active_tasks: int = 0
    last_seen: datetime
    isolation_tier: IsolationTier
    total_tasks_completed: int = 0
    success_rate: float = 0.0

class AgentsList(BaseModel):
    agents: List[AgentInfo]
    total: int
    online: int
    offline: int

# Task Schemas
class TaskInfo(BaseModel):
    task_id: str
    title: str
    agent_role: str
    tool: Optional[str] = None
    capability: Optional[str] = None
    risk_level: str
    isolation: IsolationTier
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error: Optional[str] = None

class TasksList(BaseModel):
    tasks: List[TaskInfo]
    total: int
    page: int = 1
    page_size: int = 50

# Forensic Schemas (v12.8+)
class ForensicTraceEntry(BaseModel):
    timestamp: str
    trace_id: str
    event_type: str
    component: str
    message: str
    data: Optional[Dict[str, Any]] = None

class ForensicAuditResponse(BaseModel):
    traces: List[ForensicTraceEntry]
    total: int
    file_path: str
