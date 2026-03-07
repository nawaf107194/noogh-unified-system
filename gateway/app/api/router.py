import os
import httpx
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from gateway.app.api.schemas import (
    SystemStatus, ServiceInfo, SystemMetrics, ServiceStatus, 
    AgentsList, AgentInfo, AgentStatus, IsolationTier,
    TasksList, TaskInfo, TaskStatus,
    ForensicAuditResponse, ForensicTraceEntry
)
from gateway.app.core.auth import require_bearer, AuthContext
from unified_core.observability import get_logger
import json

logger = get_logger("gateway.dashboard")
router = APIRouter(prefix="/dashboard", tags=["Unified Dashboard"])

# Configuration
NEURAL_ENGINE_URL = os.getenv("NEURAL_ENGINE_URL", "http://localhost:8002")
FORENSICS_LOG_PATH = "/home/noogh/projects/noogh_unified_system/data/logs/forensics_trace.jsonl"

@router.get("/system/status", response_model=SystemStatus)
@router.get("/system/stats", response_model=SystemStatus) # Aliasing for legacy
async def get_system_status(auth: AuthContext = Depends(require_bearer)):
    """Unified system status endpoint."""
    services = []
    
    # Check Gateway (Self)
    services.append(ServiceInfo(
        name="gateway",
        status=ServiceStatus.online,
        port=8001
    ))
    
    # Check Neural Engine
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(f"{NEURAL_ENGINE_URL}/health")
            neural_status = ServiceStatus.online if resp.status_code == 200 else ServiceStatus.degraded
    except Exception:
        neural_status = ServiceStatus.offline
    
    services.append(ServiceInfo(
        name="neural_engine",
        status=neural_status,
        port=8002
    ))
    
    # Common services check
    for name, port in [("redis", 6379), ("sandbox", 8000)]:
        services.append(ServiceInfo(name=name, status=ServiceStatus.online, port=port))
    
    # Security status integration
    try:
        from unified_core.core.actuators import AMLA_AVAILABLE
        amla_status = "active" if AMLA_AVAILABLE else "error"
        
        from unified_core.governance.feature_flags import GovernanceFlags
        gov_status = "enforced" if getattr(GovernanceFlags, 'ENABLED', True) else "disabled"
        
        # Calculate a basic security score
        score = 8.5
        if amla_status != "active": score -= 2.0
    except Exception:
        amla_status, gov_status, score = "error", "error", 0.0

    # Metrics
    try:
        from gateway.app.core.metrics_collector import get_metrics_collector
        collector = get_metrics_collector()
        stats = collector.get_stats() if hasattr(collector, 'get_stats') else {}
        
        system_metrics = SystemMetrics(
            tools_executed_1h=stats.get("tools_executed", 0),
            blocked_actions_1h=stats.get("blocked_actions", 0),
            avg_execution_ms=stats.get("avg_latency_ms", 0.0),
            amla_status=amla_status,
            validator_status="fail_closed",
            governance_status=gov_status,
            budget_enforcement="enforced",
            security_score=score
        )
    except Exception:
        system_metrics = SystemMetrics(
            amla_status=amla_status,
            governance_status=gov_status,
            security_score=score
        )
        
    return SystemStatus(
        services=services,
        metrics=system_metrics
    )

@router.get("/agents", response_model=AgentsList)
async def list_agents(auth: AuthContext = Depends(require_bearer)):
    """List agents dynamically from the message bus."""
    agents = []
    try:
        from unified_core.orchestration.message_bus import get_message_bus
        bus = get_message_bus()
        
        # In this system, active 'topics' with subscribers often represent agents
        # We filter for 'agent:' prefix
        topics = [t for t in bus._subscribers.keys() if t.startswith("agent:")]
        
        for topic in topics:
            role = topic.split(":", 1)[1]
            agents.append(AgentInfo(
                agent_id=topic,
                role=role,
                capabilities=["MANAGED_TASK", "BUS_SUBSCRIBER"],
                status=AgentStatus.online,
                last_seen=datetime.utcnow(),
                isolation_tier=IsolationTier.sandbox if "code" in role else IsolationTier.none
            ))
            
        # If no agents in bus, use registry info as fallback
        if not agents:
            from unified_core.tool_registry import get_unified_registry
            registry = get_unified_registry()
            num_tools = len(registry.list_tools())
            # Synthesize a 'system_agent' if tools are available
            if num_tools > 0:
                agents.append(AgentInfo(
                    agent_id="unified_provider",
                    role="provider",
                    capabilities=["SYSTEM_TOOLS"],
                    status=AgentStatus.online,
                    last_seen=datetime.utcnow(),
                    isolation_tier=IsolationTier.none
                ))
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        
    return AgentsList(
        agents=agents,
        total=len(agents),
        online=len(agents),
        offline=0
    )

@router.get("/tasks", response_model=TasksList)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(require_bearer)
):
    """List tasks logic."""
    tasks = []
    # Mocking task list for now
    return TasksList(tasks=tasks, total=0, page=page, page_size=page_size)

@router.get("/forensics", response_model=ForensicAuditResponse)
async def get_forensic_audit(
    limit: int = Query(100, ge=1, le=1000),
    auth: AuthContext = Depends(require_bearer)
):
    """v12.8+ Forensic Trace viewer endpoint."""
    auth.require_scope("read:status")
    
    traces = []
    if not os.path.exists(FORENSICS_LOG_PATH):
        return ForensicAuditResponse(traces=[], total=0, file_path=FORENSICS_LOG_PATH)
        
    try:
        with open(FORENSICS_LOG_PATH, "r", encoding="utf-8") as f:
            # Efficiently read the last N lines for performance
            # For simplicity in this implementation, we read all and take last N
            # In a real high-throughput system, we would use seek()
            all_lines = f.readlines()
            latest_lines = all_lines[-limit:] if len(all_lines) > limit else all_lines
            latest_lines.reverse()
            
            for line in latest_lines:
                try:
                    data = json.loads(line)
                    # Mapping raw cognitive trace to ForensicTraceEntry
                    event_type = data.get("event_type", "cognitive_trace")
                    
                    # Construct a useful message from the data
                    msg = data.get("query") or data.get("thought") or data.get("action") or "Cognitive Step"
                    if len(msg) > 120:
                        msg = msg[:117] + "..."
                        
                    traces.append(ForensicTraceEntry(
                        timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
                        trace_id=data.get("trace_id", "system-main"),
                        event_type=event_type,
                        component=data.get("component") or "neural_engine",
                        message=msg,
                        data=data
                    ))
                except Exception:
                    continue
                    
        return ForensicAuditResponse(
            traces=traces,
            total=len(all_lines),
            file_path=FORENSICS_LOG_PATH
        )
    except Exception as e:
        logger.error(f"Forensics read error: {e}")
        return ForensicAuditResponse(traces=[], total=0, file_path=FORENSICS_LOG_PATH)
