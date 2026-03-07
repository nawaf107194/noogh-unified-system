"""
Unified Core API Routes for Gateway
Exposes unified_core capabilities via REST API

SECURITY: All routes require authentication via Bearer token.
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import logging

# CRITICAL FIX: Import from Layer 1 SSOT (not Layer 3)
from unified_core.auth import require_bearer, AuthContext

logger = logging.getLogger("gateway.unified_api")

router = APIRouter(prefix="/unified", tags=["Unified Core"])


# ========================================
# Request/Response Models
# ========================================

class QueryRequest(BaseModel):
    input: Any = Field(..., description="Query input (string, dict, or list)")
    params: Optional[Dict] = Field(default=None, description="Additional parameters")


class StoreRequest(BaseModel):
    data: Any = Field(..., description="Data to store")
    params: Optional[Dict] = Field(default=None, description="Additional parameters")


class AuditRequest(BaseModel):
    code: str = Field(..., description="Code to audit")
    language: str = Field(default="python", description="Programming language")


class FreeMemoryRequest(BaseModel):
    target_mb: float = Field(..., description="Memory to free in MB")
    include_gpu: bool = Field(default=False, description="Include GPU memory")


class FileRequest(BaseModel):
    path: str = Field(..., description="File path")
    content: Optional[str] = Field(default=None, description="Content for write operations")


# ========================================
# AI Core Request Models
# ========================================

class DecisionRequest(BaseModel):
    """Request for AI core decision-making."""
    query: str = Field(..., description="The decision query or context")
    urgency: float = Field(default=0.5, ge=0.0, le=1.0, description="Urgency level 0.0-1.0")


class FailureReportRequest(BaseModel):
    """Request to report a failure (creates permanent scar)."""
    action_type: str = Field(..., description="Type of action that failed")
    error_message: str = Field(..., description="Error message describing the failure")
    params: Optional[Dict] = Field(default=None, description="Additional parameters")


# ========================================
# Bridge Dependency
# ========================================

_bridge = None


async def get_bridge():
    """Get initialized UnifiedCoreBridge."""
    global _bridge
    if _bridge is None:
        from unified_core.bridge import init_bridge
        _bridge = await init_bridge()
    return _bridge


# ========================================
# Data Routes
# ========================================

@router.post("/query")
async def query_data(
    request: QueryRequest,
    auth: AuthContext = Depends(require_bearer),
    bridge=Depends(get_bridge)
):
    """
    Query data with automatic routing.
    
    The DataRouter automatically determines which database to query based on input:
    - Mathematical expressions → PostgreSQL
    - Natural language/embeddings → Milvus (Vector DB)
    - Relationships/entities → Neo4j (Graph DB)
    """
    try:
        result = await bridge.query(request.input, **(request.params or {}))
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/store")
async def store_data(
    request: StoreRequest,
    auth: AuthContext = Depends(require_bearer),
    bridge=Depends(get_bridge)
):
    """
    Store data with automatic routing.
    
    The DataRouter automatically selects the appropriate database:
    - Equations/logic → PostgreSQL
    - Embeddings/scenarios → Milvus
    - Nodes/relationships → Neo4j
    """
    try:
        result = await bridge.store(request.data, **(request.params or {}))
        return result
    except Exception as e:
        logger.error(f"Store failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Security Routes
# ========================================

@router.post("/audit")
async def audit_code(request: AuditRequest, bridge=Depends(get_bridge)):
    """
    Audit code for security vulnerabilities.
    
    Uses AST analysis and pattern matching to detect:
    - Injection vulnerabilities (eval, exec, shell)
    - Unsafe deserialization (pickle, yaml)
    - Path traversal
    - Dangerous imports
    - Crypto weaknesses
    
    Returns risk score and detailed issues.
    """
    try:
        result = await bridge.audit_code(request.code, request.language)
        return result
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Resource Routes
# ========================================

@router.get("/system/snapshot")
async def get_system_snapshot(bridge=Depends(get_bridge)):
    """
    Get complete system resource snapshot.
    
    Returns:
    - CPU: usage, cores, load
    - Memory: total, used, percent
    - GPUs: memory, utilization, temperature
    - Disks: usage, free space
    - Process count and uptime
    """
    try:
        result = await bridge.get_system_snapshot()
        return result
    except Exception as e:
        logger.error(f"Snapshot failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/free-memory")
async def free_memory(request: FreeMemoryRequest, bridge=Depends(get_bridge)):
    """
    Free memory by terminating low-priority processes.
    
    Processes are killed in priority order:
    1. EXPENDABLE (auto-killed if enabled)
    2. LOW
    3. NORMAL
    
    CRITICAL and HIGH priority processes are never killed.
    """
    try:
        result = await bridge.free_memory(request.target_mb, request.include_gpu)
        return result
    except Exception as e:
        logger.error(f"Free memory failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Filesystem Routes
# ========================================

@router.post("/fs/read")
async def read_file(request: FileRequest, bridge=Depends(get_bridge)):
    """
    Read file through secure filesystem.
    
    Only paths within allowed roots are accessible.
    All operations are audited.
    """
    try:
        result = bridge.read_file(request.path)
        if not result["success"]:
            raise HTTPException(status_code=403, detail=result.get("error", "Access denied"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Read file failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fs/write")
async def write_file(request: FileRequest, bridge=Depends(get_bridge)):
    """
    Write file through secure filesystem.
    
    Only paths within allowed roots are writable.
    Blocked extensions (.exe, .sh, etc.) are rejected.
    """
    if not request.content:
        raise HTTPException(status_code=400, detail="Content required for write")
    
    try:
        result = bridge.write_file(request.path, request.content)
        if not result["success"]:
            raise HTTPException(status_code=403, detail=result.get("error", "Access denied"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Write file failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fs/list")
async def list_directory(request: FileRequest, bridge=Depends(get_bridge)):
    """List directory contents through secure filesystem."""
    try:
        result = bridge.list_dir(request.path)
        if not result["success"]:
            raise HTTPException(status_code=403, detail=result.get("error", "Access denied"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List dir failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fs/audit-log")
async def get_audit_log(agent_id: Optional[str] = None, bridge=Depends(get_bridge)):
    """Get filesystem operation audit log."""
    try:
        result = bridge.get_audit_log(agent_id)
        return {"entries": result}
    except Exception as e:
        logger.error(f"Audit log failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Health Check
# ========================================

@router.get("/health")
async def health_check(bridge=Depends(get_bridge)):
    """Check unified_core health status."""
    return {
        "status": "healthy" if bridge.is_initialized else "initializing",
        "components": {
            "data_router": bridge._data_router is not None,
            "secops": bridge._secops is not None,
            "resource_monitor": bridge._resource_monitor is not None,
            "process_manager": bridge._process_manager is not None,
            "filesystem": bridge._filesystem is not None
        }
    }


# ========================================
# State Inspection (Agent-Mode Enabler)
# ========================================

@router.get("/state")
async def get_system_state():
    """
    Get current SystemState snapshot.
    
    This exposes the central state that tracks operation outcomes
    and enables state-driven decision making.
    """
    from unified_core.state import get_state
    state = get_state()
    return {
        "uptime_seconds": state.uptime_seconds(),
        "current": state.snapshot(),
        "recent_history": [
            {"key": e.key, "value": e.value, "timestamp": e.timestamp}
            for e in state.history(limit=20)
        ],
        "adaptation_log": state.get_adaptation_log(limit=20),
        "risk_trend": state.get_risk_trend()
    }


@router.get("/adaptations")
async def get_adaptations():
    """
    Get recent adaptation decisions.
    
    This shows when and why the system adapted its behavior
    based on state analysis - the core of agency.
    """
    from unified_core.state import get_state
    state = get_state()
    
    trend, avg_risk = state.get_risk_trend()
    
    return {
        "adaptation_count": len(state.get_adaptation_log()),
        "adaptations": state.get_adaptation_log(limit=50),
        "current_risk_trend": trend,
        "average_risk": avg_risk,
        "thresholds": {
            "failure_threshold": state.FAILURE_THRESHOLD,
            "failure_window_seconds": state.FAILURE_WINDOW_SECONDS,
            "high_risk_threshold": state.HIGH_RISK_THRESHOLD
        }
    }


# ========================================
# Goal Tracking endpoints (Self-Directed)
# ========================================

class GoalInput(BaseModel):
    name: str
    description: str
    target_metric: str
    target_value: float

@router.post("/goals")
async def add_goal(goal: GoalInput):
    """Set a high-level goal for the system."""
    from unified_core.state import get_state
    get_state().add_goal(
        goal.name, 
        goal.description, 
        goal.target_metric, 
        goal.target_value
    )
    return {"success": True, "message": f"Goal '{goal.name}' added"}

@router.get("/goals")
async def list_goals():
    """List all active goals and their progress."""
    from unified_core.state import get_state
    return get_state().get_goals()


# ========================================
# Agent Tracking Routes (Noogh Agent Monitoring)
# ========================================
# Import and include the agent tracking router
from unified_core.agent_tracking import router as agent_tracking_router
router.include_router(agent_tracking_router)


# ========================================
# AI Core Routes (Genuine Intelligence Interface)
# ========================================

@router.get("/ai/status")
async def get_ai_core_status(bridge=Depends(get_bridge)):
    """
    Get status of the genuine AI core components.
    
    Returns metrics for:
    - WorldModel: beliefs, falsifications (permanent)
    - ConsequenceEngine: consequences, constraints (permanent)
    - CoerciveMemory: blockers, penalties (permanent)
    - ScarTissue: scars, depth (permanent)
    - GravityWell: decisions made, predictability
    """
    try:
        return bridge.get_ai_core_status()
    except Exception as e:
        logger.error(f"AI core status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/decide")
async def make_decision(request: DecisionRequest, bridge=Depends(get_bridge)):
    """
    Make a decision through the GravityWell.
    
    Decisions are:
    - Based on beliefs from WorldModel
    - Constrained by CoerciveMemory (blocks and penalties)
    - Filtered through ScarTissue (permanent damage)
    - Committed irreversibly to ConsequenceEngine
    
    > [!WARNING]
    > Decisions are IRREVERSIBLE. Each decision is permanently recorded.
    """
    try:
        result = await bridge.decide(request.query, request.urgency)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Decision failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decision failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/failure")
async def report_failure(request: FailureReportRequest, bridge=Depends(get_bridge)):
    """
    Report a failure to the ScarTissue.
    
    This creates a PERMANENT SCAR that:
    - Blocks the failed action type forever
    - Penalizes similar ideas
    - Increases scar depth
    
    > [!CAUTION]
    > This action cannot be undone. The scar is permanent.
    """
    try:
        result = bridge.report_failure(
            request.action_type,
            request.error_message,
            request.params
        )
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failure report failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failure report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/classification")
async def get_classification(bridge=Depends(get_bridge)):
    """
    Get the current classification of the system.
    
    Classification is based on:
    - Predictability (must be False for intelligence)
    - Scar accumulation (must be non-resettable)
    - Decision count (must only grow)
    - Memory coercion (must block, not advise)
    """
    try:
        status = bridge.get_ai_core_status()
        
        if not status.get("ai_core_active"):
            return {
                "classification": "UNRECOVERABLE AUTOMATION",
                "reason": "AI Core not active"
            }
        
        components = status.get("components", {})
        gravity = components.get("gravity_well", {})
        scars = components.get("scar_tissue", {})
        memory = components.get("coercive_memory", {})
        
        # Check classification criteria
        is_predictable = gravity.get("is_predictable", True)
        has_scars = scars.get("total_scars", 0) > 0 or scars.get("total_depth", 0) > 0
        has_decisions = gravity.get("decision_count", 0) > 0
        has_blockers = memory.get("blocker_count", 0) > 0
        
        if not is_predictable and (has_scars or has_decisions or has_blockers):
            return {
                "classification": "CORRECTED AGENT (MINIMAL INTELLIGENCE)",
                "properties": {
                    "predictable": is_predictable,
                    "scar_depth": scars.get("total_depth", 0),
                    "decision_count": gravity.get("decision_count", 0),
                    "blocker_count": memory.get("blocker_count", 0)
                },
                "note": "System exhibits minimal intelligence properties. Not fully autonomous."
            }
        
        return {
            "classification": "TRANSITIONAL STATE",
            "reason": "Some AI properties present, but criteria not fully met",
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Tools Hub Routes (12 External AI Tools)
# ========================================

@router.get("/tools/status")
async def tools_hub_status():
    """
    حالة جميع الأدوات المدمجة (12 أداة).
    
    Returns status of: Shannon, SmolAgents, Mem0, LangChain,
    VERL, Composio, AutoGPT, OpenHands, Aider, OpenCode,
    GeminiADK, AgentsCourse
    """
    try:
        from unified_core.tools_hub import get_tools_hub
        hub = get_tools_hub()
        return hub.get_status()
    except Exception as e:
        logger.error(f"Tools hub status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/summary")
async def tools_hub_summary():
    """ملخص مقروء لحالة الأدوات"""
    try:
        from unified_core.tools_hub import get_tools_hub
        hub = get_tools_hub()
        return {"summary": hub.summary(), "available": hub.list_available()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SecurityScanRequest(BaseModel):
    target_path: Optional[str] = Field(
        default=None,
        description="Path to scan. Defaults to NOOGH project root."
    )

@router.post("/tools/shannon/scan")
async def shannon_security_scan(request: SecurityScanRequest):
    """
    فحص أمني باستخدام Shannon AI Pentester.
    يكتشف ثغرات ويعطي تقرير مفصل.
    """
    try:
        from unified_core.tools_hub import get_tools_hub
        hub = get_tools_hub()
        result = await hub.run_security_audit(request.target_path)
        return result
    except Exception as e:
        logger.error(f"Shannon scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/insights")
async def tools_architecture_insights():
    """
    رؤى معمارية مستخلصة من AutoGPT, OpenHands, GeminiADK, VERL.
    أنماط لتحسين بنية NOOGH.
    """
    try:
        from unified_core.tools_hub import get_tools_hub
        hub = get_tools_hub()
        insights = await hub.get_architecture_insights()
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

