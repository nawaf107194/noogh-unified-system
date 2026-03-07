"""
Unified FastAPI application for Noogh Hybrid AI / Noug Neural OS.
Combines public dashboard, API, and internal security features.
"""

import logging
import os
try:
    import forensics_tracer
    forensics_tracer.start_instrumentation()
except ImportError:
    pass
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

# 1) Bootstrap Secrets (Fail-Closed)
from gateway.app.security.secrets_manager import SecretsManager

load_dotenv()
SECRETS = SecretsManager.load()

from gateway.app.api.middleware import RateLimitMiddleware, RequestSizeLimitMiddleware

# Import routers and middlewares
from gateway.app.api.routes import router
from gateway.app.core.config import get_settings
from gateway.app.core.logging import setup_logging

# Optional: import internal security middlewares if available
try:
    from gateway.app.api.security_middleware import InternalRateLimiter, LocalhostOnlyMiddleware, RequestSizeLimiter

    HAS_INTERNAL_SECURITY = True
except ImportError:
    HAS_INTERNAL_SECURITY = False

setup_logging()
settings = get_settings()

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from gateway.app.core.metrics_collector import get_metrics_collector
from gateway.app.lifespan import lifespan
from gateway.app.core.health import health_probe


class ComponentMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        collector = get_metrics_collector()
        collector.record_request(
            method=request.method, path=request.url.path, duration_sec=duration, status_code=response.status_code
        )
        return response


app = FastAPI(title="Noogh Hybrid AI", version="1.1.0", lifespan=lifespan)
app.add_middleware(ComponentMetricsMiddleware)

# Dependency Injection for Secrets
app.state.secrets = SECRETS

# Initialize ConfirmationStore with secret key
import secrets as secrets_module

from gateway.app.console.confirmation_store import ConfirmationStore

CONFIRMATION_SECRET = secrets_module.token_bytes(32)
app.state.confirmation_store = ConfirmationStore(CONFIRMATION_SECRET)

# Initialize MemorySessionStore for P0.3 memory isolation
from gateway.app.core.memory_session_store import MemorySessionStore

app.state.memory_session_store = MemorySessionStore()

# Security mode: internal or public
INTERNAL_MODE = SECRETS.get("NOOGH_INTERNAL_MODE", "0") == "1"

if INTERNAL_MODE and HAS_INTERNAL_SECURITY:
    # Internal security stack
    app.add_middleware(LocalhostOnlyMiddleware)
    app.add_middleware(InternalRateLimiter, max_requests_per_minute=200)
    app.add_middleware(RequestSizeLimiter, max_bytes=10 * 1024 * 1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["X-Internal-Token", "Content-Type"],
    )
    app.include_router(router, prefix="/api/v1")
else:
    # Public mode (dashboard, limited CORS, rate limiting)
    # SECURITY: Use explicit origin allowlist in production
    ALLOWED_ORIGINS = [
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
    ]
    # Allow wildcard ONLY in development mode
    if settings.ENV_MODE == "development":
        ALLOWED_ORIGINS = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,  # FIXED: Cannot use True with wildcard origins
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.SESSION_MAX_HISTORY * 6)
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=1024 * 1024)
    app.include_router(router, prefix="/api/v1")

    # Include prompt management routes
    from gateway.app.prompts.routes import router as prompts_router

    app.include_router(prompts_router)

    # Include prompt library routes
    from gateway.app.prompts.library_routes import router as library_router

    app.include_router(library_router)

    # Include self-governing agent routes
    from neural_engine.autonomic_system.routes import router as autonomous_router
    app.include_router(autonomous_router)

    # Include WebSocket for real-time events (Unified Memory)
    from neural_engine.autonomic_system.websocket_api import router as ws_router
    app.include_router(ws_router, prefix="/api/v1")

    # Include Control API (Start/Stop Loop)
    from neural_engine.autonomic_system.control_api import router as control_router
    app.include_router(control_router, prefix="/api/v1")

    # Include ML training routes
    from gateway.app.ml.training_routes import router as training_router

    app.include_router(training_router)

    # Include reporting routes
    from gateway.app.reporting.reporting_routes import router as reporting_router

    app.include_router(reporting_router)


# Dashboard route (always available)
DASHBOARD_PATH = Path(__file__).parent.parent / "dashboard"






# Health/Readiness endpoints
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return health_probe.check_liveness()

@app.get("/ready")
@app.get("/api/ready")
async def readiness_check(response: Response):
    status = health_probe.check_readiness()
    if not status["ready"]:
        response.status_code = 503
    return status


# UC3 Console Router
from gateway.app.console.routes import router as uc3_router

app.include_router(uc3_router)

# System Routes (Control Room APIs)
# Chat is now handled by routes.py (/chat and /api/v1/chat endpoints)


from gateway.app.api.system_routes import router as system_router

app.include_router(system_router, prefix="/api/v1")

# Sovereign Dashboard Router - system monitoring and container control
# New Backend-Driven Dashboard Router (Stats & UI)
from gateway.app.api.dashboard import router as dashboard_router, public_router as dashboard_ui_router

app.include_router(dashboard_router)
app.include_router(dashboard_ui_router)

# Security Dashboard Router - Real-time security status and monitoring
from gateway.app.api.security_dashboard import router as security_dashboard_router

app.include_router(security_dashboard_router, prefix="/api")
logging.getLogger(__name__).info("✅ Security Dashboard router mounted at /api/dashboard/security/*")

# Evolution Dashboard Router - Self-improvement monitoring
from gateway.app.api.evolution_api import router as evolution_router
app.include_router(evolution_router)
logging.getLogger(__name__).info("✅ Evolution Dashboard router mounted at /api/evolution/*")

# Unified Dashboard Router (v12.9 Consolidation)
try:
    from gateway.app.api.router import router as unified_dashboard_router
    app.include_router(unified_dashboard_router, prefix="/api/v1")
    logging.getLogger(__name__).info("✅ Unified Dashboard router mounted at /api/v1/dashboard/*")
except ImportError as e:
    logging.getLogger(__name__).warning(f"Unified Dashboard not available: {e}")

# Unified Core Router - Integrates unified_core subsystems
try:
    from unified_core.api import router as unified_core_router
    app.include_router(unified_core_router, prefix="/api/v1", tags=["Unified Core"])
    logging.getLogger(__name__).info("✅ Unified Core router mounted at /api/v1/unified")
except ImportError as e:
    logging.getLogger(__name__).warning(f"Unified Core not available: {e}")


# ============================================================================
# NEURAL ENGINE PROXY - Gateway → Neural (Option C)
# GPT/Gemini Joint Decision: Preserve separation of concerns
# ============================================================================

import httpx
from fastapi import HTTPException, APIRouter

from config.ports import PORTS
NEURAL_ENGINE_URL = os.getenv("NEURAL_ENGINE_URL", f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}")


neural_router = APIRouter(prefix="/api/v1/neural", tags=["Neural Engine Proxy"])

@neural_router.get("/{path:path}")
@neural_router.post("/{path:path}")
async def neural_proxy(path: str, request: Request):
    """
    Proxy requests to Neural Engine.
    Forwards /api/v1/neural/* to http://127.0.0.1:8765/api/v1/*
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Build target URL
            # Neural has some routes at / and some at /api/v1
            if path == "health":
                target_url = f"{NEURAL_ENGINE_URL}/health"
            else:
                target_url = f"{NEURAL_ENGINE_URL}/api/v1/{path}"
            
            # Forward important headers from original request
            forward_headers = {
                "Content-Type": request.headers.get("content-type", "application/json"),
                "X-Internal-Token": request.headers.get("x-internal-token", ""),
            }
            
            # Forward request
            if request.method == "GET":
                response = await client.get(
                    target_url,
                    params=dict(request.query_params),
                    headers=forward_headers
                )
            else:
                body = await request.body()
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    content=body,
                    headers=forward_headers
                )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type="application/json"
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Neural Engine not available. Start it on port {PORTS.NEURAL_ENGINE}."
        )
    except Exception as e:
        logging.getLogger(__name__).error(f"Neural proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(neural_router)
logging.getLogger(__name__).info("✅ Neural Engine proxy mounted at /api/v1/neural/*")


# Mount static files for sovereign dashboard
STATIC_PATH = Path(__file__).parent / "static"
STATIC_PATH.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")

# Prometheus Instrumentation (disabled temporarily)
# from prometheus_fastapi_instrumentator import Instrumentator
# @app.on_event("startup")
# async def startup():
#     Instrumentator().instrument(app).expose(app)

# WebSocket endpoint (internal mode)
try:
    from gateway.app.api.websocket import handle_websocket_message, manager

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_json()
                await handle_websocket_message(websocket, data)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logging.getLogger(__name__).error(f"WebSocket error: {e}")
            manager.disconnect(websocket)

except ImportError:
    pass


if __name__ == "__main__":
    import uvicorn

    host = SECRETS.get("NOOGH_HOST")
    port = int(SECRETS.get("NOOGH_PORT"))
    logging.getLogger(__name__).info(
        f"Starting Noogh Hybrid AI on {host}:{port} (mode: {'internal' if INTERNAL_MODE else 'public'})"
    )
    uvicorn.run("gateway.app.main:app", host=host, port=port, reload=False)


from pathlib import Path
from fastapi.responses import FileResponse

@app.get("/")
@app.get("/control")
async def control():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

# Dashboard route removed per user request
# @app.get("/dashboard")
# async def dashboard():
#     """Serve the NOOGH Dashboard"""
#     return FileResponse(
#         Path(__file__).parent / "static" / "dashboard.html",
#         media_type="text/html"
#     )
