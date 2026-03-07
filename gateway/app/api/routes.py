"""
Unified API routes for Noogh Hybrid AI / Noug Neural OS.
Combines agent, neural, memory, monitoring, and metrics endpoints.
"""

import time
import uuid
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

# Agent/brain imports
from gateway.app.core.config import get_settings
from gateway.app.core.logging import get_logger, set_log_context

# Agent/brain imports (print DEBUG statements removed for security)
import hmac

from gateway.app.api.dependencies import job_store_provider
from gateway.app.api.metrics import REQUEST_COUNT, REQUEST_LATENCY, metrics_endpoint
from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext, require_bearer

# Audit logger is now lazy-loaded via get_audit_logger
from gateway.app.core.jobs import JobRequest, JobStatus

# Use Local Brain instead of Remote
from gateway.app.plugins.loader import PluginLoader
from gateway.app.security.cloudflare_access import is_mfa_verified

# Neural OS Integration (Decoupled)
# We no longer import directly from neural_engine to avoid tight coupling in Docker.
HAS_NEURAL = True  # We assume the service is available if configured

logger = get_logger("api")
from httpx import AsyncClient
router = APIRouter()
settings = get_settings()

# --- Agent/Brain Section ---
local_brain = None
agent_kernel = None
agent_controller = None
# SECURITY FIX (HIGH-005): Thread locks for singleton initialization
import threading
_brain_lock = threading.Lock()
_kernel_lock = threading.Lock()
_controller_lock = threading.Lock()


def get_brain(request: Request):
    global local_brain
    with _brain_lock:
        secrets = getattr(request.app.state, "secrets", {})
        if local_brain is None:
            from gateway.app.llm.brain_factory import create_brain

            local_brain = create_brain(secrets=secrets)
    return local_brain


def get_kernel(request: Request):
    global agent_kernel
    with _kernel_lock:
        if agent_kernel is None:
            brain = get_brain(request)
            if brain:
                secrets = getattr(request.app.state, "secrets", {})
                from gateway.app.core.sandbox import get_sandbox_service

                sandbox_url = secrets.get("NOOGH_SANDBOX_URL", "http://localhost:8001/api/v1")
                sandbox = get_sandbox_service(service_url=sandbox_url)
                from gateway.app.core.agent_kernel import KernelConfig

                agent_kernel = AgentKernel(
                    config=KernelConfig(
                        enable_learning=True,
                        enable_dream_mode=True,
                        enable_router=True,
                    ),
                    brain=brain,
                    sandbox_service=sandbox,
                )
                logger.info("AgentKernel initialized with LocalBrainService")
            else:
                logger.warning("Cannot initialize AgentKernel without brain")
                return None
    return agent_kernel


def get_controller(request: Request):
    global agent_controller
    with _controller_lock:
        if agent_controller is None:
            kernel = get_kernel(request)
            if kernel:
                from gateway.app.core.agent_controller import AgentController

                secrets = getattr(request.app.state, "secrets", {})
                agent_controller = AgentController(kernel, secrets)
                logger.info("AgentController initialized")
            else:
                return None
    return agent_controller


class TaskRequest(BaseModel):
    task: str
    max_iterations: Optional[int] = 10  # Increased for full ReAct loop
    mode: Optional[str] = None  # Optional: Let Controller decide if None


class UnifiedResponse(BaseModel):
    success: bool
    answer: str
    steps: int = 0  # Made optional with default
    confidence: Optional[Dict[str, Any]] = None
    refusal: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    security_level: str = "read"
    mfa_verified: bool = False


if HAS_NEURAL:
    # Models — imported from shared.models (single source of truth)
    from shared.models import (
        ProcessRequest, ProcessResponse,
        MemoryRequest, MemoryResponse,
        RecallRequest, RecallResponse,
    )


# --- Metrics ---
@router.get("/metrics")
async def get_metrics():
    handler = metrics_endpoint()
    return await handler()


# --- Health (Detailed) ---
@router.get("/health/detailed")
async def health_check(request: Request):
    kernel = get_kernel(request)

    status = "ok"
    agent_ready = bool(kernel)
    neural_status = "unknown"

    # Direct HTTP check to Neural Engine (decoupled mode)
    try:
        from config.ports import PORTS
        neural_url = os.getenv("NEURAL_ENGINE_URL", f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}")

        async with AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{neural_url}/health")

        if resp.status_code == 200:
            data = resp.json()
            state = data.get("status")

            if state == "healthy":
                neural_status = "ok"
            elif state in ("initializing", "loading"):
                neural_status = "starting"
            else:
                neural_status = "error"
        else:
            neural_status = "error"

    except Exception as e:
        logger.error("NEURAL HEALTH DEBUG", exc_info=True)
        neural_status = "error"

    return {
        "status": status,
        "agent_ready": agent_ready,
        "neural_engine": neural_status,
    }




# --- Agent Task Endpoint ---

# --- ADMIN AUTH & SINGLETONS ---


def require_admin(request: Request, auth: AuthContext = Depends(require_bearer)):
    # 1. Check Cloudflare MFA (Secure Route)
    if not is_mfa_verified(request):
        logger.warning("Admin access attempted without MFA")
        raise HTTPException(status_code=403, detail="Cloudflare Access MFA Required")

    # 2. Check Admin Token
    secrets = getattr(request.app.state, "secrets", {})
    admin_token = secrets.get("NOOGH_ADMIN_TOKEN")
    if not admin_token:
        logger.error("NOOGH_ADMIN_TOKEN not set in SecretsManager")
        raise HTTPException(status_code=500, detail="Server config error: admin token missing")
    if not hmac.compare_digest(auth.token, admin_token):
        logger.warning("Admin token mismatch")
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth


plugin_loader = None


def get_plugin_loader(request: Request):
    global plugin_loader
    if plugin_loader is None:
        secrets = getattr(request.app.state, "secrets", {})
        plugin_key = secrets.get("NOOGH_PLUGIN_SIGNING_KEY", "noogh-secure-key")
        plugin_loader = PluginLoader(key=plugin_key)
    return plugin_loader


# --- JOB ENDPOINTS ---


@router.post("/jobs", response_model=Dict[str, str])
async def submit_job(
    request: JobRequest, auth: AuthContext = Depends(require_admin), job_store=Depends(job_store_provider)
):
    """Submit async job. Admin only."""
    b = request.budgets
    if not b or b.max_total_time_ms <= 0 or b.max_steps <= 0:
        raise HTTPException(status_code=400, detail="Job requires explicit positive budgets")

    job_id = job_store.submit_job(request)
    logger.info(f"Job submitted: {job_id}")
    logger.info(f"Job submitted: {job_id}")
    return {"job_id": job_id, "status": "QUEUED"}


@router.get("/jobs/list")
async def list_jobs(limit: int = 50, auth: AuthContext = Depends(require_admin), job_store=Depends(job_store_provider)):
    """List recent jobs."""
    return job_store.list_jobs(limit=limit)


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, auth: AuthContext = Depends(require_admin), job_store=Depends(job_store_provider)):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, auth: AuthContext = Depends(require_admin), job_store=Depends(job_store_provider)):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = JobStatus.CANCELLED
    job_store.save_job(job)
    return {"status": "CANCELLED"}


# --- PLUGIN ENDPOINTS ---


@router.post("/plugins/refresh")
async def refresh_plugins(request: Request, auth: AuthContext = Depends(require_admin)):
    """Reload all plugins via Loader."""
    loader = get_plugin_loader(request)
    return loader.load_all()


@router.get("/plugins")
async def list_plugins(auth: AuthContext = Depends(require_admin)):
    from gateway.app.plugins.registry import PluginRegistry

    return {"plugins": PluginRegistry.get_instance().plugins, "tools": list(PluginRegistry.get_instance().tools.keys())}


@router.post("/task", response_model=UnifiedResponse)
def process_task(request: TaskRequest, fastapi_request: Request, auth: AuthContext = Depends(require_bearer)):
    """Main endpoint: Give agent a task, get result."""
    request_id = str(uuid.uuid4())
    set_log_context(request_id=request_id)

    start_time = time.time()

    # Get Controller instead of Kernel directly
    controller = get_controller(fastapi_request)

    if not controller:
        REQUEST_COUNT.labels(method="POST", endpoint="/task", http_status=503).inc()
        raise HTTPException(status_code=503, detail="Agent system not available. Check if model is loaded.")

    # Set max iterations on the kernel (accessed via controller)
    if request.max_iterations is not None:
        if not (1 <= request.max_iterations <= 15):
            raise HTTPException(status_code=400, detail="max_iterations must be between 1 and 15")
        controller.kernel.max_iterations = request.max_iterations

    try:
        # Process task through CONTROLLER
        # Controller decides mode if request.mode is None
        logger.info(f"Controller processing task: {request.task[:50]}...")

        mfa = is_mfa_verified(fastapi_request)
        result = controller.process_task(request.task, auth, force_mode=request.mode, mfa_verified=mfa)

        duration = time.time() - start_time
        REQUEST_LATENCY.labels(method="POST", endpoint="/task").observe(duration)
        REQUEST_COUNT.labels(method="POST", endpoint="/task", http_status=200).inc()

        # Audit Log
        from gateway.app.core.audit import get_audit_logger

        secrets = getattr(fastapi_request.app.state, "secrets", {})
        data_dir = secrets.get("NOOGH_DATA_DIR")
        get_audit_logger(data_dir=data_dir).log_task(
            task_id=request_id,
            input_text=request.task,
            protocol_result="success" if result.success else "failure",
            exec_summary=f"mode: {request.mode or 'auto'}, steps: {result.steps}, error: {result.error}, mfa: {mfa}",
        )

        return UnifiedResponse(
            success=result.success,
            answer=result.answer,
            steps=result.steps,
            error=result.error,
            security_level="secure" if mfa else "read",
            mfa_verified=mfa,
        )
    except Exception as e:
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(method="POST", endpoint="/task").observe(duration)
        REQUEST_COUNT.labels(method="POST", endpoint="/task", http_status=500).inc()

        logger.error(f"Task processing failed: {e}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/distill")
async def run_distillation(
    topic: str, examples: int = 5, expand: bool = False, auth: AuthContext = Depends(require_admin)
):
    """
    Trigger Knowledge Distillation: Remote (Teacher) -> Local (Student).
    """
    from gateway.app.ml.distillation import DistillationService

    secrets = getattr(request.app.state, "secrets", {})
    service = DistillationService(secrets=secrets)

    # Run in background (simple await for now, should be background task)
    logger.info(f"Starting distillation on topic: {topic} (expand={expand})")
    result = await service.run_distillation_cycle(topic, examples, expand=expand)

    return {
        "status": "completed" if result.get("success") else "failed",
        "details": result,
        "message": f"Trained local model on '{topic}' using DeepSeek-generated data.",
    }


class SpecializationRequest(BaseModel):
    domains: Optional[List[str]] = None


@router.post("/specialization/start")
async def start_specialization(request: SpecializationRequest, auth: AuthContext = Depends(require_admin)):
    """
    Trigger the Integrated Specialization Cycle (8 Weeks).
    """
    domains = request.domains
    from gateway.app.ml.specialization import SpecializationService

    secrets = getattr(fastapi_request.app.state, "secrets", {})
    service = SpecializationService(secrets=secrets)

    # Run in background (simple await for now, should be background task)
    logger.info(f"Starting integrated specialization for domains: {domains}")
    result = await service.trigger_specialization({"domains": domains})

    return {
        "status": "initiated",
        "details": result,
        "message": "Integrated Specialization Cycle started across requested domains.",
    }


# --- Neural OS Endpoints ---
if HAS_NEURAL:

    def require_dashboard_auth(
        request: Request,
        authorization: Optional[str] = Header(None)
    ) -> AuthContext:
        """Custom auth dependency for dashboard (strict)."""
        return require_bearer(request, authorization)

    @router.post("/process", response_model=ProcessResponse)
    async def process_input(request: ProcessRequest, req: Request, auth: AuthContext = Depends(require_dashboard_auth)):
        try:
            kernel = get_kernel(req)
            orchestrator = getattr(req.app.state, "orchestrator", None)
            if not kernel and not orchestrator:
                raise HTTPException(status_code=503, detail="Neural service not available")

            # P0.3: Derive user scope and get/create memory session
            user_scope = "admin" if "*" in auth.scopes else "service" if "memory:rw" in auth.scopes else "readonly"

            # Get or create memory session (from header or create new)
            session_store = req.app.state.memory_session_store
            provided_session = req.headers.get("X-Memory-Session-ID")
            memory_session_id = session_store.get_or_create_session(
                token=auth.token, user_scope=user_scope, session_id=provided_session
            )

            # Pass session context to neural processing
            # Check if Neural Orchestrator is available locally (Monolith Bypass)
            orchestrator = getattr(req.app.state, "orchestrator", None)

            if orchestrator:
                # Direct local call (No HTTP, No Loop)
                result = await orchestrator.process(
                    input_data=request.text,
                    user_intent=request.context.get("intent", "") if request.context else "",
                )
                
                # Convert PipelineResult to ProcessResponse
                return ProcessResponse(
                    conclusion=str(result.output),
                    confidence=result.metadata.get("confidence", 1.0),
                    reasoning_trace=result.stages_completed,
                    suggested_actions=[],
                    memories_recalled=None 
                )
            
            # Fallback to Neural Client (Remote/Distributed)
            # Pass session context inside 'context' dict since client doesn't support direct args
            full_context = request.context or {}
            full_context.update({
                "session_id": memory_session_id,
                "user_scope": user_scope
            })

            response = await kernel.neural_client.process_cognition(
                text=request.text,
                context=full_context,
                store_memory=request.store_memory,
            )

            # Track memory operation
            if request.store_memory and response.success:
                logger.info(f"Memory stored for session {memory_session_id}")

            if not response.success:
                raise HTTPException(status_code=500, detail=response.error)

            return ProcessResponse(**response.data)
        except Exception as e:
            logger.error(f"Cognition error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/memory", response_model=MemoryResponse)
    async def store_memory(request: MemoryRequest, req: Request, auth: AuthContext = Depends(require_bearer)):
        kernel = get_kernel(req)

        # P0.3: Get memory session
        user_scope = "admin" if "*" in auth.scopes else "service" if "memory:rw" in auth.scopes else "readonly"
        session_store = req.app.state.memory_session_store
        memory_session_id = session_store.get_or_create_session(
            auth.token, user_scope, req.headers.get("X-Memory-Session-ID")
        )

        response = await kernel.neural_client.store_memory(
            request.content, request.metadata, session_id=memory_session_id, user_scope=user_scope
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        session_store.increment_memory_count(memory_session_id)
        return MemoryResponse(**response.data)

    @router.post("/recall", response_model=RecallResponse)
    async def recall_memories(request: RecallRequest, req: Request, auth: AuthContext = Depends(require_bearer)):
        kernel = get_kernel(req)

        # P0.3: Get memory session for recall filtering
        user_scope = "admin" if "*" in auth.scopes else "service" if "memory:rw" in auth.scopes else "readonly"
        session_store = req.app.state.memory_session_store
        memory_session_id = session_store.get_or_create_session(
            auth.token, user_scope, req.headers.get("X-Memory-Session-ID")
        )

        response = await kernel.neural_client.recall_memory(
            request.query, request.n_results, session_id=memory_session_id, user_scope=user_scope
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        return RecallResponse(**response.data)

    @router.get("/execute")
    async def execute_command(command: str, req: Request, auth: AuthContext = Depends(require_admin)):
        kernel = get_kernel(req)
        response = await kernel.neural_client.execute_command(command)
        return response.data if response.success else {"error": response.error}


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = 10


@router.post("/execute")
async def execute_code_endpoint(request: ExecuteRequest, auth: AuthContext = Depends(require_admin)):
    """
    Execute code in the Local Docker Sandbox.
    """
    from gateway.app.core.docker_sandbox import get_local_sandbox

    sandbox = get_local_sandbox()
    return sandbox.execute_code(request.code, request.language, request.timeout)

@router.get("/system_status")
async def system_status(req: Request, auth: AuthContext = Depends(require_bearer)):
    kernel = get_kernel(req)
    response = await kernel.neural_client.health_check()
    return response.data if response.success else {"status": "error", "message": response.error}

@router.get("/monitoring_dashboard")
async def get_monitoring_dashboard():
    return {"dashboard": "ok"}

@router.get("/cache_stats")
async def get_cache_stats():
    return {"cache": "ok"}

@router.post("/clear_cache")
async def clear_cache_endpoint():
    return {"cleared": True}

@router.get("/rate_limit_status")
async def get_rate_limit_status(client_id: str):
    return {"client_id": client_id, "status": "ok"}


# NOTE: /system/stats moved to gateway/app/routes/system.py (public endpoint)
# Legacy admin-only version removed to avoid route conflict.


@router.get("/analytics/stats")
async def get_analytics_stats(request: Request, auth: AuthContext = Depends(require_admin)):
    """Legacy analytics compatibility."""

    from gateway.app.core.analytics import get_analytics

    secrets = getattr(request.app.state, "secrets", {})
    data_dir = secrets.get("NOOGH_DATA_DIR")
    an = get_analytics(data_dir=data_dir)
    return an.get_system_stats()


# SECURITY FIX (MEDIUM-002): Debug print removed


@router.get("/analytics/predict")
async def predict_job(request: Request, job_type: str, auth: AuthContext = Depends(require_admin)):
    """Predict cost for a job type."""
    from gateway.app.core.analytics import get_analytics

    secrets = getattr(request.app.state, "secrets", {})
    data_dir = secrets.get("NOOGH_DATA_DIR")
    an = get_analytics(data_dir=data_dir)
    return an.predict_cost(job_type)


# --- Learning / Training Endpoints ---


class TrainingRequest(BaseModel):
    topic: str
    priority: str = "high"


@router.post("/learn")
async def scheduled_learning(request: Request, payload: TrainingRequest, auth: AuthContext = Depends(require_bearer)):
    """
    Schedule a topic for specific training (User-Directed Learning).
    This adds the topic to the priority queue for the DreamWorker.
    """
    logger.info(f"Received manual training request: {payload.topic}")

    if not hasattr(request.app.state, "scheduler"):
        return {"status": "error", "message": "Scheduler not initialized"}

    scheduler = request.app.state.scheduler
    position = scheduler.add_topic(payload.topic, payload.priority)

    return {
        "status": "scheduled",
        "topic": payload.topic,
        "queue_position": position,
        "message": f"Topic '{payload.topic}' added to learning queue.",
    }


@router.get("/learn/queue")
async def get_learning_queue(request: Request):
    """View the current training checklist."""
    if not hasattr(request.app.state, "scheduler"):
        return {"status": "error", "message": "Scheduler not initialized"}

    return {"queue": request.app.state.scheduler.peek_queue()}


# P1.9: Audit Verification Endpoints
@router.get("/audit/verify")
async def verify_audit_log(auth: AuthContext = Depends(require_admin)):
    """
    P1.9: Verify integrity of HMAC-signed audit log.
    Detects tampering and chain breaks.
    """
    import os

    from gateway.app.security.hmac_logger import get_hmac_logger

    secret = os.getenv("NOOGH_AUDIT_SECRET")
    if not secret:
        # 🔒 SECURE: Fail closed if secret is missing
        raise RuntimeError("CRITICAL SECURITY ERROR: NOOGH_AUDIT_SECRET is not set!")
    
    logger = get_hmac_logger(secret.encode("utf-8"))

    result = logger.verify_log()
    return result


@router.get("/audit/event/{event_id}")
async def get_audit_event(event_id: str, auth: AuthContext = Depends(require_admin)):
    """
    P1.9: Get integrity proof for a specific audit event.
    """
    import os

    from gateway.app.security.hmac_logger import get_hmac_logger

    secret = os.getenv("NOOGH_AUDIT_SECRET")
    if not secret:
        raise RuntimeError("CRITICAL SECURITY ERROR: NOOGH_AUDIT_SECRET is not set!")
        
    logger = get_hmac_logger(secret.encode("utf-8"))

    proof = logger.get_integrity_proof(event_id)

    if proof is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return proof


# --- ORCHESTRATED CHAT ENDPOINT ---


class ChatRequest(BaseModel):
    message: str
    use_reasoning: Optional[bool] = False
    context: Optional[Dict[str, Any]] = None


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, fastapi_request: Request, auth: AuthContext = Depends(require_bearer)):
    """
    Orchestrated Chat Endpoint.
    Routes user messages through the Neural Orchestrator -> LocalBrainBridge.
    Falls back to direct Neural Engine API call.
    """
    # SECURITY FIX (MEDIUM-002): Debug print removed - was exposing user messages
    
    # 1. Get Orchestrator
    orchestrator = getattr(fastapi_request.app.state, "orchestrator", None)

    if not orchestrator:
        # Fallback to direct Neural Engine API call
        logger = get_logger("api")
        logger.warning("Orchestrator not found, falling back to direct Neural Engine API")
        
        import httpx
        secrets = getattr(fastapi_request.app.state, "secrets", {})
        internal_token = secrets.get("NOOGH_INTERNAL_TOKEN", "")
        neural_url = secrets.get("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")
        
        logger.info("🔑 Using token from secrets: ***")
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{neural_url}/api/v1/process",
                    headers={
                        "Content-Type": "application/json",
                        "X-Internal-Token": internal_token
                    },
                    json={"text": request.message, "context": request.context or {}}
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "response": data.get("conclusion", ""),
                        "status": "success",
                        "mode": "neural_engine_direct"
                    }
                else:
                    return {
                        "response": f"Neural Engine Error: {response.status_code}",
                        "status": "error",
                        "mode": "neural_engine_direct"
                    }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Neural Engine Error: {e}")

    try:
        # 2. Process via Neural Pipeline
        # Merge context if provided
        prompt_context = {"use_reasoning": request.use_reasoning}
        if request.context:
            prompt_context.update(request.context)

        pipeline_result = await orchestrator.process(
            input_data=request.message, 
            user_intent="chat_interaction", 
            require_validation=False,
            prompt_context=prompt_context
        )

        if pipeline_result.success:
            return {
                "response": str(pipeline_result.output),
                "status": "success",
                "mode": "neural_orchestrator",
                "metadata": pipeline_result.metadata,
            }
        else:
            return {
                "response": "I apologize, but I encountered an error processing your thought.",
                "status": "error",
                "error": str(pipeline_result.errors),
            }

    except Exception as e:
        logger = get_logger("api")
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Neural Processing Error")
