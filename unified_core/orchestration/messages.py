"""
NOOGH Orchestration Messages

Message envelope and types for inter-agent communication via Message Bus.

SECURITY: All messages MUST contain full tracing and risk metadata.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageType(Enum):
    """Message types for orchestration bus"""
    REQUEST = "REQUEST"  # Agent requests action
    RESULT = "RESULT"  # Response with result
    EVENT = "EVENT"  # System event
    ERROR = "ERROR"  # Error notification
    ACK = "ACK"  # Acknowledgment


class RiskLevel(Enum):
    """Risk classification for operations"""
    SAFE = "SAFE"  # Read-only, no side effects
    RESTRICTED = "RESTRICTED"  # Code exec in sandbox, allowlist writes
    DANGEROUS = "DANGEROUS"  # System commands, network, sensitive writes


class AgentRole(Enum):
    """Agent roles in the system"""
    ORCHESTRATOR = "orchestrator"
    CODE_EXECUTOR = "code_executor"
    SECURITY_MONITOR = "security_monitor"
    RESEARCH_AGENT = "research_agent"
    FILE_MANAGER = "file_manager"
    MEMORY_AGENT = "memory_agent"
    MONITOR = "monitor"
    # Auto-generated agent roles
    HEALTH_MONITOR = "health_monitor"
    LOG_ANALYZER = "log_analyzer"
    # Brain-designed agent roles
    PERFORMANCE_PROFILER = "performance_profiler"
    DEPENDENCY_AUDITOR = "dependency_auditor"
    TEST_RUNNER = "test_runner"
    BACKUP_AGENT = "backup_agent"
    WEB_RESEARCHER = "web_researcher"
    PIPELINE_OPTIMIZER = "pipeline_optimizer"
    RESEARCH_SPECIALIST = "research_specialist"
    SALES_AUTOMATION = "sales_automation"
    AUTONOMOUS_TRADING_AGENT = "autonomous_trading_agent"


@dataclass
class MessageEnvelope:
    """
    Standard message envelope for all inter-agent communication.
    
    CRITICAL: All fields are REQUIRED for security tracing.
    """
    # Identifiers
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default="")  # Links related messages
    task_id: str = field(default="")  # Links to task in DAG
    
    # Routing
    sender: str = field(default="")  # Format: "role:instance_id"
    receiver: str = field(default="")  # Format: "role:instance_id" or "role:*"
    
    # Classification
    type: MessageType = field(default=MessageType.REQUEST)
    risk_level: RiskLevel = field(default=RiskLevel.SAFE)
    
    # Authorization
    scopes: List[str] = field(default_factory=list)  # Required scopes
    
    # Content
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    ttl_ms: int = field(default=30000)  # Time to live
    retry_count: int = field(default=0)
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.trace_id:
            raise ValueError("trace_id is REQUIRED")
        if not self.task_id:
            raise ValueError("task_id is REQUIRED")
        if not self.sender:
            raise ValueError("sender is REQUIRED")
        if not self.receiver:
            raise ValueError("receiver is REQUIRED")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "message_id": self.message_id,
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type.value,
            "risk_level": self.risk_level.value,
            "scopes": self.scopes,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "ttl_ms": self.ttl_ms,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageEnvelope':
        """Create from dictionary"""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            trace_id=data["trace_id"],
            task_id=data["task_id"],
            sender=data["sender"],
            receiver=data["receiver"],
            type=MessageType(data["type"]),
            risk_level=RiskLevel(data["risk_level"]),
            scopes=data.get("scopes", []),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", time.time()),
            ttl_ms=data.get("ttl_ms", 30000),
            retry_count=data.get("retry_count", 0)
        )
    
    def is_expired(self) -> bool:
        """Check if message has exceeded TTL"""
        elapsed_ms = (time.time() - self.timestamp) * 1000
        return elapsed_ms > self.ttl_ms
    
    def create_reply(
        self,
        type: MessageType,
        payload: Dict[str, Any],
        risk_level: Optional[RiskLevel] = None
    ) -> 'MessageEnvelope':
        """Create a reply to this message"""
        return MessageEnvelope(
            trace_id=self.trace_id,
            task_id=self.task_id,
            sender=self.receiver,  # Swap sender/receiver
            receiver=self.sender,
            type=type,
            risk_level=risk_level or self.risk_level,
            scopes=self.scopes,
            payload=payload
        )


@dataclass
class ToolRequest:
    """Request for tool execution via UnifiedToolRegistry"""
    tool_name: str
    arguments: Dict[str, Any]
    isolation: str = "none"  # none | sandbox | lab_container
    timeout_ms: int = 10000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "isolation": self.isolation,
            "timeout_ms": self.timeout_ms
        }
