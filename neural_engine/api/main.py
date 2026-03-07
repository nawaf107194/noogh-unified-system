"""
FastAPI application for Noug Neural OS.
Provides REST API endpoints to interact with the neural system.

SECURITY NOTE: This service is designed for INTERNAL use only.
- Binds to 127.0.0.1 (localhost) by default
- CORS restricted to NOOGH gateway
- Requires internal token for sensitive endpoints
"""

import logging
import os
# try:
#     import forensics_tracer
#     forensics_tracer.start_instrumentation()
# except ImportError:
#     pass

# CRITICAL: Prevent CUDA memory fragmentation - ENABLED for 12GB GPU
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True,max_split_size_mb:128"

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from neural_engine.api.routes import router
from neural_engine.api.security_middleware import (
    InternalRateLimiter,
    LocalhostOnlyMiddleware,
)
from neural_engine.api.websocket import handle_websocket_message, manager

# Load environment variables from .env if it exists
from dotenv import load_dotenv
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
elif os.path.exists(".env"):
    load_dotenv(".env")

# Setup logging
try:
    from observability_suite.logger import setup_logging

    setup_logging("NougAPI")
except ImportError:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Noug Neural OS API",
    version="1.1.0",
    description="Biologically-inspired Neural Operating System API (Internal Service)",
)

# Security middleware stack (order matters - first added = last executed)
# 1. Localhost only restriction (outermost - checked first)
app.add_middleware(LocalhostOnlyMiddleware)

# 2. Rate limiting
app.add_middleware(InternalRateLimiter, max_requests_per_minute=200)

# 3. CORS - restricted to NOOGH gateway only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",  # Gateway
        "http://127.0.0.1:8001",  # Gateway
        "http://localhost:8080",  # Dashboard
        "http://127.0.0.1:8080",  # Dashboard
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["X-Internal-Token", "Content-Type", "X-Trace-Id", "Authorization"],
)

# 4. Tracing (Top-level Context Injection)
from neural_engine.api.tracing_middleware import TracingMiddleware
app.add_middleware(TracingMiddleware)

from fastapi import Request
from fastapi.responses import JSONResponse
import uuid

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    logger.error(f"Global Exception [TraceID: {trace_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal System Error",
            "message": "An unexpected error occurred. Please contact support.",
            "trace_id": trace_id
        },
    )

# Include routers
app.include_router(router, prefix="/api/v1")

# Specialized Systems Router (autonomous_learning, ai_model_manager, creative_studio)
try:
    from neural_engine.specialized_systems.routes import router as specialized_router
    app.include_router(specialized_router, prefix="/api/v1")
    logger.info("✅ Specialized Systems router mounted")
except ImportError as e:
    logger.warning(f"Specialized Systems not available: {e}")

# Autonomic Control API
try:
    from neural_engine.autonomic_system.control_api import router as autonomic_router
    app.include_router(autonomic_router, prefix="/api/v1")
    logger.info("✅ Autonomic Control API mounted")
except ImportError as e:
    logger.warning(f"Autonomic Control API not available: {e}")

# Event Stream API
try:
    from neural_engine.autonomic_system.event_api import router as event_router
    app.include_router(event_router, prefix="/api/v1")
    logger.info("✅ Event Stream API mounted")
except ImportError as e:
    logger.warning(f"Event Stream API not available: {e}")

# Self-Awareness API
try:
    from neural_engine.autonomic_system.self_awareness_api import router as awareness_router
    app.include_router(awareness_router, prefix="/api/v1")
    logger.info("✅ Self-Awareness API mounted")
except ImportError as e:
    logger.warning(f"Self-Awareness API not available: {e}")

# WebSocket API
try:
    from neural_engine.autonomic_system.websocket_api import router as ws_router
    app.include_router(ws_router, prefix="/api/v1")
    logger.info("✅ WebSocket API mounted")
except ImportError as e:
    logger.warning(f"WebSocket API not available: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Noug Neural OS",
        "version": "1.1.0",
        "status": "operational",
        "mode": "internal-service",
        "description": "Biologically-inspired Neural Operating System API",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with model status."""
    from neural_engine.model_authority import get_model_authority
    authority = get_model_authority()
    model_info = authority.get_loaded_model_info()
    
    return {
        "status": "healthy" if model_info["state"] == "LOADED" else "initializing",
        "mode": "internal",
        "model": model_info,
        "components": {
            "memory": "operational", 
            "reasoning": "operational" if model_info["state"] == "LOADED" else "pending",
            "api": "operational"
        },
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.

    Usage:
        ws = new WebSocket('ws://localhost:8000/ws');
        ws.send(JSON.stringify({type: 'ping'}));
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(websocket, data)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


# Startup logic
_startup_executed = False

@app.on_event("startup")
async def startup():
    """Initialize system on startup - EAGER MODEL LOADING"""
    global _startup_executed
    if _startup_executed:
        return
    _startup_executed = True
    
    import os
    logger.info("✅ Neural Engine started - Loading model immediately...")
    
    from neural_engine.model_authority import get_model_authority
    authority = get_model_authority()
    
    model_path = os.getenv("NOOGH_MODEL")
    backend = os.getenv("NOOGH_BACKEND", "local-gpu")
    
    if model_path:
        logger.info(f"🔧 Model Authority: Enabled (LAZY loading for {backend} - will load on first request)")
        # Explicit CUDA initialization to prevent handle errors
        if backend == "local-gpu":
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.init()
                    # Clear CUDA cache to free fragmented memory
                    torch.cuda.empty_cache()
                    # Set memory limit for MoE model (naturally efficient)
                    torch.cuda.set_per_process_memory_fraction(0.60, device=0)  # 60% of 12GB = 7.2GB
                    free_mem = torch.cuda.mem_get_info()[0] / 1024**3
                    logger.info(f"✅ CUDA Initialized: {torch.cuda.get_device_name(0)} | Free: {free_mem:.2f} GB | Limit: 7.2GB (MoE optimized)")
                else:
                    logger.warning("⚠️ CUDA requested but not available")
            except Exception as e:
                logger.error(f"❌ CUDA Error during startup: {e}")
        # DISABLED: Eager loading disabled to avoid OOM during startup
        # Model will load lazily on first inference request
        # authority.load_model(backend=backend, model_name=model_path)
    else:
        logger.info(f"🔧 Model Authority: UNLOADED (backend={backend})")


if __name__ == "__main__":
    import uvicorn

    # PERFORMANCE: Support Unix Domain Sockets for fastest local communication
    uds = os.getenv("NEURAL_UDS")
    host = os.getenv("NEURAL_HOST", "127.0.0.1")
    port = int(os.getenv("NEURAL_PORT", "8002"))

    if uds:
        logger.info(f"🚀 Starting Noug Neural OS on Unix Socket: {uds} (MAX PERFORMANCE)")
        uvicorn.run(
            app,
            uds=uds,
            reload=False,
            workers=1,
            log_level="info",
        )
    else:
        logger.info(f"Starting Noug Neural OS on {host}:{port} (internal service)")
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            workers=1,
            log_level="info",
        )
