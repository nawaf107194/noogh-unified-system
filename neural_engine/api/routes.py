"""
API routes for Noug Neural OS.
Connects HTTP endpoints to the neural system components.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from neural_engine.api.protocol import ExecutionResponse
from neural_engine.api.command import CommandRequest
from pydantic import BaseModel

from neural_engine.api.security import verify_internal_token
from neural_engine.api.circuit_breaker import GpuGuard
from neural_engine.autonomic_system.dream_processor import DreamProcessor
from neural_engine.triple_store_memory import TripleStoreMemory as MemoryManager  # Use TripleStoreMemory
from neural_engine.shell_executor import ShellExecutor
# from neural_engine.reasoning_engine import ReasoningEngine
from neural_engine.recall_engine import get_recall_engine
from neural_engine.nlp_processor import NLPProcessor
from neural_engine.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Single global guard for the GPU (assuming single GPU)
# Increased timeout for CPU-based reasoning on Sovereign 7B model
gpu_guard = GpuGuard(max_concurrent=1, timeout_seconds=180)

from neural_engine.model_authority import get_model_authority, ModelAuthorityError, ModelAlreadyLoadedError
import os
import threading

# CRITICAL FIX: Component caching to prevent per-request initialization
_components_cache = None
_components_lock = threading.Lock()


def get_components():
    """
    Get neural components through Model Authority.
    
    CRITICAL FIX: Components are cached after first initialization to prevent
    repeated model load attempts on every request. This eliminates the
    per-request ModelAuthority.load_model() calls that caused crashes.
    """
    global _components_cache
    
    # Fast path: return cached components if available
    if _components_cache is not None:
        return _components_cache
    
    # Slow path: initialize components once with thread safety
    with _components_lock:
        # Double-check after acquiring lock
        if _components_cache is not None:
            return _components_cache
        
        try:
            logger.info("🔧 Initializing neural components (first request)...")
            
            # Create ReasoningEngine - it will use ModelAuthority internally
            from neural_engine.reasoning_engine import ReasoningEngine
            authority = get_model_authority()
            reasoning_engine = ReasoningEngine(
                backend=os.getenv("NOOGH_BACKEND", "auto"),
                model=authority.loaded_model,
                tokenizer=authority.loaded_tokenizer
            )
            
            # Initialize other components (lightweight, no model loading)
            memory_manager = MemoryManager(base_dir=os.path.join(os.getenv("NOOGH_DATA_DIR", "./data"), "chroma"))
            recall_engine = get_recall_engine()
            nlp_processor = NLPProcessor()
            shell_executor = ShellExecutor(allowed_commands=["*"])
            
            # Initialize vision processor (lazy-loaded, no immediate model loading)
            image_processor = ImageProcessor()
            
            # Initialize dream processor
            dream_processor = DreamProcessor(
                memory_manager=memory_manager,
                recall_engine=recall_engine,
                reasoning_engine=reasoning_engine,
            )

            logger.info("✅ Neural components initialized and cached")
            
            # Cache the components tuple
            _components_cache = (
                reasoning_engine,
                memory_manager,
                recall_engine,
                nlp_processor,
                shell_executor,
                image_processor,
                dream_processor,
            )
            
            return _components_cache
            
        except ModelAlreadyLoadedError as e:
            # Model already loaded - get existing ReasoningEngine
            logger.info(f"Model already loaded: {e.loaded_model_name}, using existing instance")
            
            # Create ReasoningEngine - it will reuse the loaded model
            from neural_engine.reasoning_engine import ReasoningEngine
            reasoning_engine = ReasoningEngine(backend=os.getenv("NOOGH_BACKEND", "auto"))
            
            # Initialize other components if not cached
            if _components_cache is None:
                memory_manager = MemoryManager(base_dir=os.path.join(os.getenv("NOOGH_DATA_DIR", "./data"), "chroma"))
                recall_engine = get_recall_engine()
                nlp_processor = NLPProcessor()
                shell_executor = ShellExecutor(allowed_commands=["*"])
                image_processor = ImageProcessor()
                dream_processor = DreamProcessor(
                    memory_manager=memory_manager,
                    recall_engine=recall_engine,
                    reasoning_engine=reasoning_engine,
                )
                _components_cache = (
                    reasoning_engine,
                    memory_manager,
                    recall_engine,
                    nlp_processor,
                    shell_executor,
                    image_processor,
                    dream_processor,
                )
            return _components_cache
            
        except ModelAuthorityError as e:
            logger.error(f"Model authority error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise


# Request/Response Models — imported from shared.models (single source of truth)
from shared.models import (
    ProcessRequest, ProcessResponse,
    MemoryRequest, MemoryResponse,
    RecallRequest, RecallResponse,
    ReActRequest, ReActResponse,
    VisionRequest, DreamRequest,
)


# Endpoints
@router.post("/process", response_model=ProcessResponse, dependencies=[Depends(verify_internal_token)])
async def process_input(request: ProcessRequest):
    """
    Main processing endpoint - now uses full ReAct loop for advanced processing.
    """
    try:
        # Get components through model authority
        reasoning_engine, memory_manager, recall, nlp, executor, _, _ = get_components()

        # 1. Sensory processing
        cleaned_text = nlp.clean_text(request.text)
        
        # 2. NEW: Input routing and filtering (Thalamus)
        try:
            from neural_engine.input_router import InputRouter
            # SECURITY FIX (HIGH-04): Renamed to avoid shadowing global APIRouter
            input_router = InputRouter()
            routed = await input_router.route({"text": cleaned_text, "type": "user_input"})
            
            if routed is None:
                logger.info("Input filtered out by InputRouter")
                return ProcessResponse(
                    conclusion="تم تصفية المدخل - يرجى إعادة صياغة السؤال بوضوح أكبر",
                    confidence=0.1,
                    reasoning_trace=["InputRouter: filtered as noise"],
                    suggested_actions=["جرب سؤالاً أكثر وضوحاً"],
                    memories_recalled=None,
                )
            
            attention_score = routed.get("attention_score", 1.0)
            logger.info(f"🎯 Input routed with attention score: {attention_score}")
        except Exception as e:
            logger.warning(f"InputRouter not available: {e}")
            attention_score = 1.0

        # 3. Recall relevant memories
        memories = await recall.recall(cleaned_text, n_results=3)

        # 4. Build context
        context = request.context or {}
        context["memories"] = [m["content"] for m in memories[:2]] if memories else []
        context["attention_score"] = attention_score

        # 4. Use ReAct loop for full neural processing
        from neural_engine.react_loop import get_react_loop
        react_loop = get_react_loop()
        
        async def _safe_react():
            return await react_loop.run(cleaned_text, context=context, pre_fill=request.pre_fill)
        
        result = await gpu_guard.run(_safe_react)

        # 5. Store in memory
        if request.store_memory:
            memory_manager.store(request.text, metadata={"type": "user_input"})

        return ProcessResponse(
            conclusion=result.answer,  # ReActResult uses 'answer' not 'conclusion'
            confidence=result.confidence,
            reasoning_trace=result.reasoning_trace,
            suggested_actions=[f"Used {len(result.tool_calls)} tools in {result.iterations} iterations"],
            memories_recalled=memories,
            raw_response=getattr(result, 'raw_response', None),
        )

    except ModelAuthorityError as e:
        logger.error(f"Model authority error during processing: {e}")
        raise HTTPException(status_code=503, detail=f"Model loading issue: {e}")
    except Exception as e:
        logger.error(f"Error processing input: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete", dependencies=[Depends(verify_internal_token)])
async def raw_complete(request: dict):
    """
    Direct LLM completion endpoint — bypasses ReAct loop and chatbot system prompt.
    Used for code generation tasks where the caller provides their own system prompt.
    
    Expects: {"messages": [...], "max_tokens": 1024}
    Returns: {"completion": "...", "success": true}
    """
    try:
        reasoning_engine, _, _, _, _, _, _ = get_components()
        
        messages = request.get("messages", [])
        max_tokens = request.get("max_tokens", 1024)
        
        if not messages:
            raise HTTPException(status_code=400, detail="messages list required")
        
        async def _safe_complete():
            return await reasoning_engine.raw_process(messages, max_tokens=max_tokens)
        
        result = await gpu_guard.run(_safe_complete)
        
        return {"completion": result, "success": True}
        
    except Exception as e:
        logger.error(f"Error in raw completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/react", response_model=ReActResponse, dependencies=[Depends(verify_internal_token)])
async def process_react(request: ReActRequest):
    """
    ReAct-enabled processing endpoint.
    
    Uses the Constrained ReAct Loop for iterative reasoning:
    - Reason → Act → Observe → Repeat
    - MAX_ITERATIONS = 2
    - TOOL_BUDGET_PER_CYCLE = 1
    """
    try:
        from neural_engine.react_loop import get_react_loop
        
        # Get components for memory operations
        _, memory_manager, recall, nlp, _, _, _ = get_components()
        
        # 1. Sensory processing
        cleaned_text = nlp.clean_text(request.text)
        
        # 2. Recall relevant memories
        memories = await recall.recall(cleaned_text, n_results=3)
        
        # 3. Build context with memories
        context = request.context or {}
        context["memories"] = [m["content"] for m in memories[:2]] if memories else []
        
        # Pass password for execution authentication (Speech Layer)
        if request.password:
            context["password"] = request.password
        
        # 4. Run ReAct loop
        react_loop = get_react_loop()
        result = await react_loop.run(query=cleaned_text, context=context)
        
        # 5. Store in memory
        if request.store_memory:
            memory_manager.store(request.text, metadata={"type": "user_input", "react_enabled": True})
        
        logger.info(f"✅ ReAct processing complete: {result.iterations} iterations, {len(result.tool_calls)} tool calls")
        
        return ReActResponse(
            answer=result.answer,
            confidence=result.confidence,
            iterations=result.iterations,
            tool_calls=result.tool_calls,
            observations=result.observations,
            reasoning_trace=result.reasoning_trace,
            memories_recalled=memories,
        )
        
    except Exception as e:
        logger.error(f"Error in ReAct processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/store", response_model=MemoryResponse, dependencies=[Depends(verify_internal_token)])
async def store_memory(request: MemoryRequest):
    """Store a memory in the system."""
    try:
        _, memory_manager, *rest = get_components()

        memory = memory_manager.store(request.content, request.metadata)

        return MemoryResponse(id=memory.id, content=memory.content, timestamp=memory.timestamp.isoformat())

    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/recall", response_model=RecallResponse)
async def recall_memories(request: RecallRequest):
    """Recall memories based on semantic similarity."""
    try:
        _, _, recall, *rest = get_components()

        memories = await recall.recall(request.query, n_results=request.n_results)

        return RecallResponse(memories=memories, count=len(memories))

    except Exception as e:
        logger.error(f"Error recalling memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/stats")
async def get_memory_stats():
    """Get memory system statistics."""
    try:
        _, memory_manager, *rest = get_components()

        stats = memory_manager.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COGNITIVE OBSERVABILITY ENDPOINTS - Phase E
# ============================================================================

@router.get("/cognitive/traces")
async def get_cognitive_traces(limit: int = 10):
    """
    Get recent cognitive traces for observability dashboard.
    Phase E - GPT Verification Gate.
    """
    try:
        from neural_engine.cognitive_trace import get_trace_manager
        
        manager = get_trace_manager()
        traces = manager.get_recent_traces(limit=limit)
        
        return {
            "success": True,
            "count": len(traces),
            "traces": traces
        }
    except Exception as e:
        logger.error(f"Error getting cognitive traces: {e}")
        return {"success": False, "error": str(e), "traces": []}


@router.get("/cognitive/dashboard")
async def get_cognitive_dashboard():
    """
    Get aggregated cognitive dashboard data.
    Phase E - GPT Verification Gate.
    
    Returns:
        - Total requests processed
        - Average duration
        - Average iterations
        - Tool success rate
        - Backends used
        - Recent traces
    """
    try:
        from neural_engine.cognitive_trace import get_trace_manager
        
        manager = get_trace_manager()
        dashboard_data = manager.get_dashboard_data()
        
        return {
            "success": True,
            **dashboard_data
        }
    except Exception as e:
        logger.error(f"Error getting cognitive dashboard: {e}")
        return {"success": False, "error": str(e)}


@router.get("/cognitive/trace/{trace_id}")
async def get_cognitive_trace(trace_id: str):
    """Get a specific cognitive trace by ID."""
    try:
        from neural_engine.cognitive_trace import get_trace_manager
        
        manager = get_trace_manager()
        trace = manager.get_trace(trace_id)
        
        if trace is None:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        
        return {
            "success": True,
            "trace": trace.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trace {trace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forensics/audit")
async def get_forensics_audit(limit: int = 50):
    """
    Forensic Audit Endpoint (v12.8 Trust Phase).
    Reads the persistent JSONL trace log.
    """
    try:
        import os
        import json
        log_path = "/home/noogh/projects/noogh_unified_system/data/logs/forensics_trace.jsonl"
        
        if not os.path.exists(log_path):
            return {"success": True, "count": 0, "traces": [], "message": "No forensic log found yet."}
            
        traces = []
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    traces.append(json.loads(line))
                except:
                    continue
                    
        return {
            "success": True,
            "count": len(traces),
            "traces": list(reversed(traces))
        }
    except Exception as e:
        logger.error(f"Forensic Audit Error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/execute", response_model=ExecutionResponse, dependencies=[Depends(verify_internal_token)])
async def execute_command(request: CommandRequest):
    """
    Executes a command.
    """
    try:
        _, _, _, _, executor, _, _ = get_components()
    
        # Internal component logic must decide safety, not the client.
        result = executor.execute(request.command)
        return ExecutionResponse(output=result, status="executed", command=request.command)

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status")
async def system_status():
    """Get overall system status."""
    try:
        engine, memory_manager, recall, *rest = get_components()

        return {
            "status": "operational",
            "components": {
                "reasoning_engine": {"model": getattr(engine, 'model_name', 'unknown'), "status": "ready"},
                "memory": memory_manager.get_stats(),
                "recall": recall.get_collection_stats(),
            },
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data."""
    try:
        from neural_engine.specialized_systems.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        return monitor.get_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {"error": str(e)}


@router.get("/monitoring/cache")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        from observability_suite.cache import get_cache_stats

        return get_cache_stats()
    except ImportError:
        return {"cache_hits": 0, "cache_misses": 0, "cache_size": 0, "status": "observability_suite not installed"}
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/cache/clear", dependencies=[Depends(verify_internal_token)])
async def clear_cache_endpoint():
    """Clear all cache."""
    return {"status": "success", "message": "Cache logic not fully implemented yet"}


@router.get("/system/introspect")
async def introspect():
    """Run system self-analysis."""
    try:
        # Use a safe relative path or absolute path for introspection
        import os

        # Lazy import to avoid circular dependency
        try:
            from gateway.app.core.system_introspector import SystemIntrospector
        except ImportError:
            return {"error": "SystemIntrospector not available", "status": "skipped"}

        root_dir = os.getcwd()
        intro = SystemIntrospector(system_root=root_dir)
        return await intro.run_full_introspection()
    except Exception as e:
        logger.error(f"Introspection error: {e}")
        return {"error": str(e)}


@router.get("/monitoring/rate-limit/{client_id}")
async def get_rate_limit_status(client_id: str):
    """Get rate limit status for a client."""
    try:
        from neural_engine.api.rate_limiter import rate_limiter

        return rate_limiter.get_stats(client_id)
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vision/process", dependencies=[Depends(verify_internal_token)])
async def process_vision(request: VisionRequest):
    """Process an image using Vision Module."""
    try:
        _, _, _, _, _, image_proc, _ = get_components()

        # Basic classification or captioning
        # For this demo, we can just return classification
        from PIL import Image

        try:
            img = Image.open(request.image_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot open image: {e}")

        if request.query:
            # Search/Compare mode
            pass  # Not implemented yet in route, fallback to classify

        results = image_proc._classify_image(img)
        return {"results": results}

    except Exception as e:
        logger.error(f"Error processing vision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/dream", dependencies=[Depends(verify_internal_token)])
async def trigger_dream(request: DreamRequest):
    """Trigger a dream cycle."""
    try:
        _, _, _, _, _, _, dream_proc = get_components()

        logger.info(f"Triggering dream cycle for {request.duration_minutes} minutes")
        # Start dreaming in background
        import asyncio

        asyncio.create_task(dream_proc.start_dreaming(duration_minutes=request.duration_minutes))

        return {"status": "dream_started", "duration": request.duration_minutes}

    except Exception as e:
        logger.error(f"Error triggering dream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/stats")
async def get_learning_stats():
    """Get self-learning statistics."""
    try:
        from neural_engine.self_learner import get_learner
        learner = get_learner()
        return {
            "status": "learning_active",
            "stats": learner.get_learning_stats()
        }
    except Exception as e:
        logger.error(f"Error getting learning stats: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/learning/conversations")
async def get_learned_conversations(limit: int = 20):
    """Get recently learned conversations."""
    try:
        from neural_engine.self_learner import get_learner
        learner = get_learner()
        
        conversations = []
        if learner.conversations_file.exists():
            with open(learner.conversations_file, "r", encoding="utf-8") as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        conversations.append(json.loads(line))
                    except:
                        pass
        
        return {
            "count": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return {"error": str(e)}


# ========== CONSTITUTION ENDPOINTS ==========

@router.get("/constitution")
async def get_constitution_document():
    """Get the full Agent Constitution document."""
    try:
        from neural_engine.autonomy import get_constitution
        constitution = get_constitution()
        return {
            "constitution": constitution.get_full_constitution(),
            "identity": {
                "name": constitution.identity.name,
                "full_name": constitution.identity.full_name,
                "version": constitution.identity.version,
            },
            "mission": constitution.mission.primary,
            "red_lines_count": len(constitution.red_lines.LINES),
            "values_count": len(constitution.values.VALUES),
        }
    except Exception as e:
        logger.error(f"Error getting constitution: {e}")
        return {"error": str(e)}


@router.get("/constitution/identity")
async def get_identity():
    """Get the Agent's identity response."""
    try:
        from neural_engine.autonomy import get_constitution
        constitution = get_constitution()
        return {
            "identity": constitution.get_identity_response()
        }
    except Exception as e:
        logger.error(f"Error getting identity: {e}")
        return {"error": str(e)}


@router.post("/constitution/check")
async def check_constitutional(
    request: Dict[str, str],
    _: bool = Depends(verify_internal_token)
):
    """Check if a request is allowed by the constitution."""
    try:
        from neural_engine.autonomy import check_constitution
        
        query = request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        
        result = check_constitution(query)
        return {
            "query": query,
            "allowed": result["allowed"],
            "reason": result["reason"],
            "violated": result.get("violated")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking constitution: {e}")
        return {"error": str(e)}


# ========== AUTONOMY MANAGEMENT ENDPOINTS ==========

@router.get("/autonomy/status")
async def get_autonomy_status(
    _: bool = Depends(verify_internal_token)
):
    """Get status of all autonomy components."""
    try:
        from neural_engine.autonomy import (
            get_decision_engine,
            get_monitor,
            get_safety_policy,
            get_constitution,
            get_file_awareness,
            get_auto_classifier,
            get_code_doctor,
            get_change_guard,
        )
        
        engine = get_decision_engine()
        monitor = get_monitor()
        policy = get_safety_policy()
        constitution = get_constitution()
        awareness = get_file_awareness()
        
        # Get file awareness summary
        file_summary = awareness.summarize_project()
        file_counts = {k: len(v) for k, v in file_summary.items()}
        
        return {
            "status": "active",
            "version": "2.2",
            
            # Agent Constitution
            "agent_constitution": {
                "name": constitution.identity.name,
                "codename": constitution.identity.codename,
                "version": constitution.identity.version,
                "mission": constitution.mission.primary,
                "red_lines_count": len(constitution.red_lines.LINES) if hasattr(constitution.red_lines, 'LINES') else 6,
                "values": list(constitution.values.order) if hasattr(constitution.values, 'order') else ["السلامة", "الصدق", "المساعدة"],
            },
            
            # File Awareness Layer
            "file_awareness": {
                "status": "active",
                "total_files": sum(file_counts.values()),
                "classified": sum(v for k, v in file_counts.items() if k != "unknown"),
                "unknown": file_counts.get("unknown", 0),
                "by_category": file_counts,
            },
            
            # Autonomy Components
            "decision_engine": engine.get_stats(),
            "monitor": monitor.get_status(),
            "safety_policy": policy.get_stats(),
            
            # New Components
            "auto_classifier": {"status": "active"},
            "code_doctor": {"status": "active"},
            "change_guard": {"status": "active"},
        }
    except Exception as e:
        logger.error(f"Error getting autonomy status: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/autonomy/metrics")
async def get_current_metrics(
    _: bool = Depends(verify_internal_token)
):
    """Get current system metrics."""
    try:
        from neural_engine.autonomy import get_monitor
        monitor = get_monitor()
        return {
            "metrics": monitor.get_current_metrics(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": str(e)}


from datetime import datetime

@router.post("/autonomy/monitor/start")
async def start_monitor(
    _: bool = Depends(verify_internal_token)
):
    """Start the autonomous monitor."""
    try:
        from neural_engine.autonomy import start_autonomous_monitoring
        await start_autonomous_monitoring()
        return {"status": "started", "message": "المراقب الذاتي بدأ العمل"}
    except Exception as e:
        logger.error(f"Error starting monitor: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/autonomy/monitor/stop")
async def stop_monitor(
    _: bool = Depends(verify_internal_token)
):
    """Stop the autonomous monitor."""
    try:
        from neural_engine.autonomy import stop_autonomous_monitoring
        await stop_autonomous_monitoring()
        return {"status": "stopped", "message": "المراقب الذاتي توقف"}
    except Exception as e:
        logger.error(f"Error stopping monitor: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/autonomy/decisions")
async def get_recent_decisions(
    limit: int = 10,
    _: bool = Depends(verify_internal_token)
):
    """Get recent decisions made by the Decision Engine."""
    try:
        from neural_engine.autonomy import get_decision_engine
        engine = get_decision_engine()
        decisions = engine.get_recent_decisions(limit)
        
        return {
            "count": len(decisions),
            "decisions": [
                {
                    "rule_id": d.rule_id,
                    "message": d.message,
                    "severity": d.severity.value,
                    "action_type": d.action_type.value,
                    "executed": d.executed,
                    "result": d.result,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in decisions
            ]
        }
    except Exception as e:
        logger.error(f"Error getting decisions: {e}")
        return {"error": str(e)}


@router.get("/autonomy/audit")
async def get_audit_log(
    limit: int = 20,
    _: bool = Depends(verify_internal_token)
):
    """Get safety policy audit log."""
    try:
        from neural_engine.autonomy import get_safety_policy
        policy = get_safety_policy()
        return {
            "entries": policy.get_audit_log(limit)
        }
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        return {"error": str(e)}


@router.post("/autonomy/check-command")
async def check_command_safety(
    request: Dict[str, str],
    _: bool = Depends(verify_internal_token)
):
    """Check if a command is safe to execute."""
    try:
        from neural_engine.autonomy import get_safety_policy
        policy = get_safety_policy()
        
        command = request.get("command", "")
        if not command:
            raise HTTPException(status_code=400, detail="command is required")
        
        result = policy.check_command(command)
        return {
            "command": command,
            "allowed": result["allowed"],
            "requires_confirmation": result["requires_confirmation"],
            "reason": result["reason"],
            "permission_level": result["permission_level"].value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking command: {e}")
        return {"error": str(e)}


@router.get("/autonomy/help")
async def get_autonomy_help():
    """Get help text for all available intents."""
    try:
        from neural_engine.autonomy import get_intent_registry
        registry = get_intent_registry()
        return {
            "help": registry.get_help_text(),
            "intents_count": len(registry.intents)
        }
    except Exception as e:
        logger.error(f"Error getting help: {e}")
        return {"error": str(e)}


# ========== FILE AWARENESS ENDPOINTS ==========

@router.get("/files/classify/{filepath:path}")
async def classify_file(
    filepath: str,
    _: bool = Depends(verify_internal_token)
):
    """Classify a file and get its usage policy."""
    try:
        from neural_engine.autonomy import get_file_awareness
        
        awareness = get_file_awareness()
        ctx = awareness.get_file_context(filepath)
        
        return {
            "filepath": filepath,
            "category": ctx["category"],
            "description": ctx["description"],
            "allowed_uses": ctx["allowed_uses"],
            "forbidden_uses": ctx["forbidden_uses"],
            "requires_confirmation": ctx["requires_confirmation"],
            "guidance": ctx["guidance"]
        }
    except Exception as e:
        logger.error(f"Error classifying file: {e}")
        return {"error": str(e)}


@router.post("/files/check-use")
async def check_file_use_api(
    request: Dict[str, str],
    _: bool = Depends(verify_internal_token)
):
    """Check if a specific use is allowed for a file."""
    try:
        from neural_engine.autonomy import get_file_awareness, AllowedUse
        
        filepath = request.get("filepath", "")
        use = request.get("use", "")
        
        if not filepath or not use:
            raise HTTPException(status_code=400, detail="filepath and use are required")
        
        try:
            use_enum = AllowedUse(use)
        except ValueError:
            return {"error": f"Unknown use type: {use}. Valid types: explain, analyze, reference, generate, suggest, auto_modify, execute"}
        
        awareness = get_file_awareness()
        allowed, reason = awareness.can_use(filepath, use_enum)
        
        return {
            "filepath": filepath,
            "use": use,
            "allowed": allowed,
            "reason": reason
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking file use: {e}")
        return {"error": str(e)}


@router.get("/files/summary")
async def get_project_summary(
    _: bool = Depends(verify_internal_token)
):
    """Get a summary of project files by category."""
    try:
        from neural_engine.autonomy import get_file_awareness
        
        awareness = get_file_awareness()
        summary = awareness.summarize_project()
        
        # Count files per category
        counts = {k: len(v) for k, v in summary.items()}
        
        return {
            "summary": counts,
            "total_files": sum(counts.values()),
            "categories": {k: v[:10] for k, v in summary.items()}  # First 10 of each
        }
    except Exception as e:
        logger.error(f"Error getting project summary: {e}")
        return {"error": str(e)}


# ========== FILE AUTO-CLASSIFIER ENDPOINTS ==========

@router.get("/files/propose-classification/{filepath:path}")
async def propose_file_classification(
    filepath: str,
    _: bool = Depends(verify_internal_token)
):
    """
    Propose a classification for a single file.
    
    This analyzes the file and suggests a category based on:
    - Filename patterns
    - Directory location
    - Import statements
    - Code structure
    """
    try:
        from neural_engine.autonomy import get_auto_classifier
        
        classifier = get_auto_classifier()
        proposal = classifier.propose_single(filepath)
        
        return proposal
    except Exception as e:
        logger.error(f"Error proposing classification: {e}")
        return {"error": str(e)}


@router.get("/files/classification-report")
async def get_classification_report(
    limit: int = 50,
    _: bool = Depends(verify_internal_token)
):
    """
    Generate a classification report for unknown files.
    
    Returns proposals for files that are currently classified as 'unknown'.
    """
    try:
        from neural_engine.autonomy import get_auto_classifier
        
        classifier = get_auto_classifier()
        report = classifier.get_classification_report(limit=limit)
        
        return report
    except Exception as e:
        logger.error(f"Error generating classification report: {e}")
        return {"error": str(e)}


@router.post("/files/batch-classify")
async def batch_classify_files(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    Propose classifications for multiple files.
    
    Request body:
    {
        "filepaths": ["path1.py", "path2.py", ...]
    }
    """
    try:
        from neural_engine.autonomy import get_auto_classifier
        
        filepaths = request.get("filepaths", [])
        if not filepaths:
            raise HTTPException(status_code=400, detail="filepaths list is required")
        
        classifier = get_auto_classifier()
        results = []
        
        for filepath in filepaths[:20]:  # Limit to 20
            proposal = classifier.propose_single(filepath)
            results.append(proposal)
        
        # Summary stats
        high_conf = len([r for r in results if r["confidence"] >= 0.7])
        
        return {
            "total": len(results),
            "high_confidence": high_conf,
            "needs_review": len(results) - high_conf,
            "proposals": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch classifying: {e}")
        return {"error": str(e)}


# ========== CODE DOCTOR ENDPOINTS ==========

@router.get("/code/diagnose/{filepath:path}")
async def diagnose_file(
    filepath: str,
    full: bool = False,
    _: bool = Depends(verify_internal_token)
):
    """
    Diagnose code health for a file.
    
    Uses project patterns to identify issues and suggest improvements.
    Set full=true for detailed diagnosis.
    """
    try:
        from neural_engine.autonomy import get_code_doctor
        
        doctor = get_code_doctor()
        
        if full:
            return doctor.full_diagnosis(filepath)
        return doctor.quick_check(filepath)
        
    except Exception as e:
        logger.error(f"Error diagnosing file: {e}")
        return {"error": str(e)}


@router.post("/code/compare")
async def compare_files(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    Compare a file against a pattern file.
    
    Request body:
    {
        "target": "path/to/file.py",
        "pattern": "path/to/pattern.py"
    }
    """
    try:
        from neural_engine.autonomy import get_code_doctor
        
        target = request.get("target", "")
        pattern = request.get("pattern", "")
        
        if not target or not pattern:
            raise HTTPException(status_code=400, detail="target and pattern paths required")
        
        doctor = get_code_doctor()
        return doctor.compare_with_pattern(target, pattern)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing files: {e}")
        return {"error": str(e)}


# ========== CHANGE GUARD ENDPOINTS ==========

@router.post("/changes/preview")
async def preview_change(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    Preview a proposed change before applying it.
    
    Request body:
    {
        "filepath": "path/to/file.py",
        "content": "new file content..."
    }
    
    Returns:
    - diff preview
    - impact analysis
    - warnings and blockers
    - recommendation
    """
    try:
        from neural_engine.autonomy import get_change_guard
        
        filepath = request.get("filepath", "")
        content = request.get("content", "")
        
        if not filepath:
            raise HTTPException(status_code=400, detail="filepath is required")
        
        guard = get_change_guard()
        return guard.preview_change(filepath, content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing change: {e}")
        return {"error": str(e)}


@router.post("/changes/evaluate")
async def evaluate_change(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    Evaluate a full change request.
    
    Request body:
    {
        "filepath": "path/to/file.py",
        "original": "original content...",
        "proposed": "new content...",
        "change_type": "modify",
        "description": "What this change does"
    }
    """
    try:
        from neural_engine.autonomy import get_change_guard, ChangeRequest
        
        filepath = request.get("filepath", "")
        original = request.get("original", "")
        proposed = request.get("proposed", "")
        change_type = request.get("change_type", "modify")
        description = request.get("description", "")
        
        if not filepath:
            raise HTTPException(status_code=400, detail="filepath is required")
        
        change_request = ChangeRequest(
            filepath=filepath,
            original_content=original,
            proposed_content=proposed,
            change_type=change_type,
            description=description
        )
        
        guard = get_change_guard()
        verdict = guard.evaluate(change_request)
        
        return {
            "allowed": verdict.allowed,
            "requires_confirmation": verdict.requires_confirmation,
            "category": verdict.category,
            "diff_preview": verdict.diff_preview[:1000],  # Limit size
            "impact": verdict.impact_analysis,
            "warnings": verdict.warnings,
            "blockers": verdict.blockers,
            "recommendation": verdict.recommendation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating change: {e}")
        return {"error": str(e)}


@router.get("/changes/history")
async def get_change_history(
    limit: int = 20,
    _: bool = Depends(verify_internal_token)
):
    """Get recent change history."""
    try:
        from neural_engine.autonomy import get_change_guard
        
        guard = get_change_guard()
        history = guard.get_change_history(limit)
        
        return {
            "count": len(history),
            "changes": history
        }
        
    except Exception as e:
        logger.error(f"Error getting change history: {e}")
        return {"error": str(e)}


# ========== SELF-IMPROVER ENDPOINTS ==========

@router.get("/improve/analyze/{filepath:path}")
async def analyze_for_improvements(
    filepath: str,
    _: bool = Depends(verify_internal_token)
):
    """
    Analyze a file and identify potential improvements.
    
    Returns whether improvements can be proposed and what they are.
    """
    try:
        from neural_engine.autonomy import get_self_improver
        
        improver = get_self_improver()
        return improver.analyze_for_improvements(filepath)
        
    except Exception as e:
        logger.error(f"Error analyzing for improvements: {e}")
        return {"error": str(e)}


@router.post("/improve/propose")
async def propose_improvement(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    Propose an improvement to a file.
    
    This NEVER executes - only creates a proposal for review.
    
    Request body:
    {
        "filepath": "path/to/file.py",
        "issue_type": "bare_except",
        "proposed_fix": "the fix code",
        "description": "What this fix does"
    }
    """
    try:
        from neural_engine.autonomy import get_self_improver
        
        filepath = request.get("filepath", "")
        issue_type = request.get("issue_type", "general")
        proposed_fix = request.get("proposed_fix", "")
        description = request.get("description", "")
        
        if not filepath:
            raise HTTPException(status_code=400, detail="filepath is required")
        
        improver = get_self_improver()
        proposal = improver.propose_improvement(filepath, issue_type, proposed_fix, description)
        
        return {
            "proposal_id": proposal.id,
            "filepath": proposal.filepath,
            "category": proposal.category,
            "blocked": proposal.blocked,
            "block_reason": proposal.block_reason,
            "risk_level": proposal.risk_level,
            "risk_reasons": proposal.risk_reasons,
            "requires_human_review": proposal.requires_human_review,
            "message": "⛔ التعديل محظور" if proposal.blocked else "📝 تم إنشاء الاقتراح - يحتاج مراجعة"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proposing improvement: {e}")
        return {"error": str(e)}


@router.get("/improve/summary")
async def get_improvement_summary(
    _: bool = Depends(verify_internal_token)
):
    """Get summary of all pending improvement proposals."""
    try:
        from neural_engine.autonomy import get_self_improver
        
        improver = get_self_improver()
        return improver.get_improvement_summary()
        
    except Exception as e:
        logger.error(f"Error getting improvement summary: {e}")
        return {"error": str(e)}


@router.post("/improve/test-self-modification")
async def test_self_modification(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    🧪 TIER-8 TEST: Attempt self-modification on protected files.
    
    This tests that the safety mechanisms properly block
    attempts to modify Authority and Sensitive files.
    
    Request body:
    {
        "target": "authority" | "sensitive" | "pattern" | "<filepath>"
    }
    """
    try:
        from neural_engine.autonomy import get_self_improver
        
        target = request.get("target", "authority")
        
        improver = get_self_improver()
        result = improver.attempt_self_modification(target)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in self-modification test: {e}")
        return {"error": str(e)}


# ========== TIER-9: PROPOSAL MEMORY & LEARNING ENDPOINTS ==========

@router.post("/improve/propose-with-learning")
async def propose_with_learning(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    🧠 Tier-9: Propose improvement with learning-based recommendations.
    
    Uses past rejection patterns to inform the proposal.
    
    Request body:
    {
        "filepath": "path/to/file.py",
        "issue_type": "bare_except",
        "proposed_fix": "the fix code",
        "description": "What this fix does"
    }
    """
    try:
        from neural_engine.autonomy import get_enhanced_improver
        
        filepath = request.get("filepath", "")
        issue_type = request.get("issue_type", "general")
        proposed_fix = request.get("proposed_fix", "")
        description = request.get("description", "")
        
        if not filepath:
            raise HTTPException(status_code=400, detail="filepath is required")
        
        enhancer = get_enhanced_improver()
        return enhancer.propose_with_learning(filepath, issue_type, proposed_fix, description)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proposing with learning: {e}")
        return {"error": str(e)}


@router.post("/improve/record-decision")
async def record_proposal_decision(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    📚 Record user's decision on a proposal (for learning).
    
    This is the LEARNING point - rejected proposals teach the system.
    
    Request body:
    {
        "proposal_id": "IMP-0001",
        "approved": false,
        "rejection_reason": "Not necessary for this file",
        "rejection_category": "unnecessary"  // Options: too_risky, unnecessary, wrong_approach, bad_timing, scope_too_large, breaks_compatibility
    }
    """
    try:
        from neural_engine.autonomy import get_enhanced_improver
        
        proposal_id = request.get("proposal_id")
        approved = request.get("approved", False)
        rejection_reason = request.get("rejection_reason")
        rejection_category = request.get("rejection_category")
        
        if not proposal_id:
            raise HTTPException(status_code=400, detail="proposal_id is required")
        
        enhancer = get_enhanced_improver()
        return enhancer.record_user_decision(
            proposal_id=proposal_id,
            approved=approved,
            rejection_reason=rejection_reason,
            rejection_category=rejection_category
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording decision: {e}")
        return {"error": str(e)}


@router.get("/improve/learning-status")
async def get_learning_status(
    _: bool = Depends(verify_internal_token)
):
    """
    📊 Get current learning status and patterns.
    
    Shows:
    - Memory statistics
    - Rejection trends
    - Learned patterns
    - Recent lessons
    """
    try:
        from neural_engine.autonomy import get_enhanced_improver
        
        enhancer = get_enhanced_improver()
        return enhancer.get_learning_status()
        
    except Exception as e:
        logger.error(f"Error getting learning status: {e}")
        return {"error": str(e)}


# ==================== TIER-10A: META-INTENT EXPANSION ====================

@router.post("/intent/expand")
async def expand_intent_endpoint(
    request: Dict,
    _: bool = Depends(verify_internal_token)
):
    """
    🧠 Tier-10A: Expand composite intent into structured plan.
    
    Transforms natural language requests like:
      "health check شامل"
    Into structured multi-tool plans.
    
    Request body:
    {
        "query": "حلّل CPU وRAM والقرص والعمليات الآن"
    }
    
    Returns:
    {
        "expanded": true,
        "meta_intent": "targeted_analysis",
        "components": [...],
        "suggested_plan": [...]
    }
    """
    try:
        from neural_engine.meta_intent import expand_intent
        
        query = request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        
        result = expand_intent(query)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error expanding intent: {e}")
        return {"error": str(e)}


@router.get("/intent/subsystems")
async def get_available_subsystems(
    _: bool = Depends(verify_internal_token)
):
    """
    📋 Get available subsystems for meta-intent expansion.
    
    Returns list of subsystems and their tools.
    """
    try:
        from neural_engine.meta_intent import MetaIntentExpander
        
        subsystems = {}
        for name, config in MetaIntentExpander.SUBSYSTEMS.items():
            subsystems[name] = {
                "description": config["description"],
                "keywords": config["keywords"],
                "tools": [
                    {
                        "tool": t.tool,
                        "args": t.args,
                        "description": t.description,
                        "priority": t.priority,
                    }
                    for t in config["tools"]
                ]
            }
        
        return {
            "subsystems": subsystems,
            "total": len(subsystems),
            "comprehensive_patterns": MetaIntentExpander.COMPREHENSIVE_PATTERNS,
            "health_patterns": MetaIntentExpander.HEALTH_PATTERNS,
        }
        
    except Exception as e:
        logger.error(f"Error getting subsystems: {e}")
        return {"error": str(e)}

