# gateway/app/routes/system.py
"""
System routes for Control Room:
- /system/stats - System statistics (GPU, CPU, RAM)
- /system/logs/stream - SSE live log streaming via Loki
- /system/logs/query - Loki log query
- /system/tools - List available tools
- /system/tools/{name}/request - Request tool execution
- /system/dream - Trigger dream cycle
- /system/health/all - Validate all services
"""
import asyncio
import os
import time
from typing import Optional

import httpx
import psutil
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from gateway.app.core.auth import AuthContext, require_bearer, require_scoped_token

router = APIRouter(tags=["System"])

# Configuration
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
NEURAL_ENGINE_URL = os.getenv("NEURAL_ENGINE_URL", "http://localhost:8002")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:8501")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

# ==============================
# Service Health Validation
# ==============================


async def check_service(url: str, timeout: float = 2.0) -> dict:
    """Check if a service is reachable."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            return {"status": "up", "code": resp.status_code}
    except Exception as e:
        return {"status": "down", "error": str(e)}


@router.get("/system/health/all")
async def validate_all_services(
    auth: AuthContext = Depends(require_bearer)
):
    """Validate all backend services (Authorized)."""
    # Ensure read:status scope
    auth.require_scope("read:status")
    results = await asyncio.gather(
        check_service("http://localhost:8001/health"),  # Gateway
        check_service(f"{NEURAL_ENGINE_URL}/health"),  # Neural Engine
        check_service(f"{PROMETHEUS_URL}/api/v1/status/runtimeinfo"),  # Prometheus
        check_service(f"{LOKI_URL}/ready"),  # Loki
        check_service(f"{GRAFANA_URL}/api/health"),  # Grafana
    )

    services = {
        "gateway": results[0],
        "neural_engine": results[1],
        "prometheus": results[2],
        "loki": results[3],
        "grafana": results[4],
    }

    all_up = all(s["status"] == "up" for s in services.values())

    return {"status": "operational" if all_up else "degraded", "services": services, "timestamp": time.time()}


# ==============================
# System Stats
# ==============================


def get_gpu_stats() -> dict:
    """Get GPU stats using torch (CHAOS-002 FIX: no subprocess)."""
    try:
        import torch

        if torch.cuda.is_available():
            gpu_idx = 0
            total_mem = torch.cuda.get_device_properties(gpu_idx).total_memory / (1024**3)
            allocated = torch.cuda.memory_allocated(gpu_idx) / (1024**3)
            free_mem = total_mem - allocated
            # Estimate utilization from memory usage
            free_raw, total_raw = torch.cuda.mem_get_info(gpu_idx)
            utilization = 1.0 - (free_raw / total_raw)
            return {
                "total_vram_gb": round(total_mem, 2),
                "free_vram_gb": round(free_mem, 2),
                "utilization": round(utilization, 3),
            }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: no GPU
    return {"total_vram_gb": 0, "free_vram_gb": 0, "utilization": 0}


async def get_neural_health() -> str:
    """Check Neural Engine health."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{NEURAL_ENGINE_URL}/health")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("status", "unknown")
    except Exception:
        pass
    return "unreachable"


@router.get("/system/stats")
async def system_stats(
    auth: AuthContext = Depends(require_bearer)
):
    """Get comprehensive system statistics (Authorized)."""
    auth.require_scope("read:status")
    gpu = get_gpu_stats()
    neural_status = await get_neural_health()

    return {
        "gpu": gpu,
        "system": {
            "cpu_usage": psutil.cpu_percent(interval=0.1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
        },
        "services": {"gateway": "ok", "neural_engine": neural_status},
        "timestamp": time.time(),
    }


# ==============================
# Logs Streaming via Loki
# ==============================


async def query_loki_tail(query: str, limit: int = 100, start_ns: int = None):
    """Query Loki for recent logs."""
    if start_ns is None:
        # Last 1 hour
        start_ns = int((time.time() - 3600) * 1e9)

    end_ns = int(time.time() * 1e9)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{LOKI_URL}/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": str(start_ns),
                    "end": str(end_ns),
                    "limit": limit,
                    "direction": "backward",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("result", [])
    except Exception as e:
        return [{"error": str(e)}]

    return []


@router.get("/system/logs/stream")
async def stream_logs(
    service: str = Query("gateway", description="Service: gateway or neural_engine"),
    level: str = Query(None, description="Filter by level: INFO, WARNING, ERROR"),
    limit: int = Query(100, description="Number of log entries"),
    auth: AuthContext = Depends(require_bearer)
):
    """Stream logs via Server-Sent Events from Loki (Authorized)."""
    auth.require_scope("read:metrics")
    
    # Restrict allowed services
    allowed_services = ["gateway", "neural_engine", "unified_core", "worker"]
    if service not in allowed_services:
        raise HTTPException(status_code=403, detail=f"Logs for service '{service}' are restricted.")
    from sse_starlette.sse import EventSourceResponse

    # Build Loki query
    base_query = f'{{job="noogh", service="{service}"}}'
    if level:
        base_query = f'{base_query} |= "{level}"'

    async def event_generator():
        last_ts = int((time.time() - 300) * 1e9)  # Start from 5 minutes ago

        # First, send historical logs
        streams = await query_loki_tail(base_query, limit=limit, start_ns=last_ts)
        for stream in streams:
            values = stream.get("values", [])
            labels = stream.get("stream", {})
            for ts, line in reversed(values):  # Reverse for chronological order
                yield {"event": "log", "data": {"ts": ts, "service": labels.get("service", "unknown"), "line": line}}
                last_ts = max(last_ts, int(ts))

        # Then, poll for new logs every 2 seconds
        while True:
            await asyncio.sleep(2)
            new_start = last_ts + 1
            streams = await query_loki_tail(base_query, limit=20, start_ns=new_start)
            for stream in streams:
                values = stream.get("values", [])
                labels = stream.get("stream", {})
                for ts, line in reversed(values):
                    yield {
                        "event": "log",
                        "data": {"ts": ts, "service": labels.get("service", "unknown"), "line": line},
                    }
                    last_ts = max(last_ts, int(ts))

    return EventSourceResponse(event_generator())


@router.get("/system/logs/query")
async def query_logs(
    query: str = '{job="noogh"}', 
    since: str = "1h", 
    limit: int = 500,
    auth: AuthContext = Depends(require_bearer)
):
    """Direct Loki query endpoint (Authorized & Restricted)."""
    auth.require_scope("read:metrics")
    
    # HARDENING: Prevent arbitrary queries (e.g. leaking secrets from other jars)
    if 'job="noogh"' not in query:
        raise HTTPException(status_code=403, detail="Only 'noogh' job logs can be queried via this endpoint.")
    
    # Prevent dangerous patterns (e.g. potential log forge/injection bypass)
    forbidden = ["password", "token", "key", "secret"]
    for f in forbidden:
        if f in query.lower():
             raise HTTPException(status_code=403, detail=f"Query contains forbidden pattern: {f}")
    # Parse since duration
    duration_map = {"1h": 3600, "6h": 21600, "24h": 86400, "1d": 86400, "7d": 604800}
    seconds = duration_map.get(since, 3600)
    start_ns = int((time.time() - seconds) * 1e9)

    streams = await query_loki_tail(query, limit=limit, start_ns=start_ns)

    # Flatten to list of log entries
    entries = []
    for stream in streams:
        labels = stream.get("stream", {})
        for ts, line in stream.get("values", []):
            entries.append(
                {
                    "timestamp": ts,
                    "service": labels.get("service", "unknown"),
                    "job": labels.get("job", ""),
                    "line": line,
                }
            )

    return {"count": len(entries), "entries": entries}


# ==============================
# Tools API
# ==============================

TOOLS_REGISTRY = [
    {"name": "remote_shell", "risk": "high", "enabled": True, "description": "Execute shell commands"},
    {"name": "memory.recall", "risk": "low", "enabled": True, "description": "Query semantic memory"},
    {"name": "memory.store", "risk": "low", "enabled": True, "description": "Store data in memory"},
    {"name": "dream.start", "risk": "low", "enabled": True, "description": "Trigger a dream cycle"},
    {"name": "http_request", "risk": "medium", "enabled": True, "description": "Make HTTP requests"},
    {"name": "train.model", "risk": "high", "enabled": True, "description": "Train/fine-tune models"},
]


class ToolRequest(BaseModel):
    reason: Optional[str] = None
    args: Optional[dict] = None
    confirm: bool = False


@router.get("/system/tools")
async def list_tools(
    auth: AuthContext = Depends(require_bearer)
):
    """List all available tools and their status (Authorized)."""
    auth.require_scope("tools:use")
    return {"tools": TOOLS_REGISTRY}


@router.post("/system/tools/{tool_name}/request")
async def request_tool(
    tool_name: str, 
    request: ToolRequest,
    auth: AuthContext = Depends(require_bearer)
):
    """Request execution of a tool (Authorized)."""
    auth.require_scope("tools:use")
    tool = next((t for t in TOOLS_REGISTRY if t["name"] == tool_name), None)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    if not tool["enabled"]:
        raise HTTPException(status_code=403, detail=f"Tool is disabled: {tool_name}")

    # High-risk tools require confirmation
    if tool["risk"] == "high" and not request.confirm:
        return {
            "status": "pending_confirmation",
            "tool": tool_name,
            "message": "⚠️ High-risk tool requires explicit confirmation. Set confirm=true to proceed.",
            "risk": tool["risk"],
        }

    # Medium-risk tools show warning but proceed
    if tool["risk"] == "medium" and not request.confirm:
        return {
            "status": "pending_confirmation",
            "tool": tool_name,
            "message": "Medium-risk tool. Confirm to proceed.",
            "risk": tool["risk"],
        }

    # Simulate tool queuing (in real system, this would use the actual tool registry)
    return {
        "status": "queued",
        "tool": tool_name,
        "reason": request.reason,
        "args": request.args,
        "message": f"✓ Tool '{tool_name}' has been queued for execution.",
        "execution_id": f"exec-{int(time.time())}",
    }


# ==============================
# Dream Management
# ==============================


class DreamRequest(BaseModel):
    minutes: int = 1


@router.post("/system/dream")
async def trigger_dream(
    request: DreamRequest,
    auth: AuthContext = Depends(require_bearer)
):
    """
    Trigger a dream cycle: Generate synthetic training data (Authorized).
    """
    auth.require_scope("admin:all")
    import json
    import time
    from gateway.app.llm.brain_factory import get_brain_service

    # Ensure dreams directory exists
    DREAMS_DIR = "/home/noogh/projects/noogh_unified_system/src/data/dreams"
    os.makedirs(DREAMS_DIR, exist_ok=True)

    brain = get_brain_service()
    
    # 1. Dream Prompt: Ask the brain to recall a useful interaction or invent one
    dream_prompt = (
        "Generate a high-quality training example for an AI assistant. "
        "Format: INSTRUCTION: <task> RESPONSE: <ideal_response>. "
        "Topic: Reasoning, Coding, or Science."
    )
    
    try:
        # Use the brain (Gemini/Local) to dream
        # brain.generate is synchronous (blocking), so no await
        dream_content = brain.generate(dream_prompt, max_new_tokens=512)
        
        # Simple parsing (robustness would require regex)
        instruction = "Unknown Instruction"
        response = dream_content
        
        if "INSTRUCTION:" in dream_content and "RESPONSE:" in dream_content:
            parts = dream_content.split("RESPONSE:")
            instruction = parts[0].replace("INSTRUCTION:", "").strip()
            response = parts[1].strip()

        # 2. Save the Dream
        timestamp = int(time.time())
        dream_entry = {
            "id": f"dream_{timestamp}",
            "instruction": instruction,
            "output": response,
            "source": "synthetic_dream_worker",
            "created_at": timestamp
        }
        
        filename = f"{DREAMS_DIR}/dream_{timestamp}.jsonl"
        with open(filename, "w") as f:
            f.write(json.dumps(dream_entry) + "\n")

        return {
            "status": "triggered",
            "dream_id": dream_entry["id"],
            "message": f"🌙 Dream generated and saved to {filename}",
            "content_preview": instruction[:50] + "..."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dream failed: {str(e)}")


# ==============================
# Internal Tasks Management
# ==============================

TASK_FILE_PATH = "/home/noogh/.gemini/antigravity/brain/02c71315-8584-4af7-bee2-1f0ecc2605e8/task.md"

@router.get("/system/tasks")
async def get_internal_tasks(
    auth: AuthContext = Depends(require_bearer)
):
    """Retrieve internal Agent tasks from task.md (Authorized)."""
    auth.require_scope("read:status")
    if not os.path.exists(TASK_FILE_PATH):
        return {"tasks": [], "raw": "No task file found."}

    try:
        with open(TASK_FILE_PATH, "r") as f:
            content = f.read()

        parsed_tasks = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("- ["):
                status_char = line[3]
                status = "pending"
                if status_char.lower() == "x":
                    status = "completed"
                elif status_char == "/":
                    status = "in_progress"
                
                text = line[5:].strip()
                parsed_tasks.append({"status": status, "text": text})

        return {
            "tasks": parsed_tasks,
            "raw": content,
            "count": len(parsed_tasks),
            "completed": len([t for t in parsed_tasks if t["status"] == "completed"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

