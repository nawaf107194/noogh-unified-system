# /home/noogh/projects/noogh_unified_system/src/gateway/app/api/dashboard.py
from __future__ import annotations

import os
import time
import json
import html
import re
import logging
import secrets
import ipaddress
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable
from urllib.parse import urlparse
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# JWT Authentication for unified auth with Dashboard API
from gateway.app.core.jwt_validator import verify_gateway_token, require_role


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
public_router = APIRouter(tags=["dashboard-ui"])

# Analytics
from gateway.app.analytics.kpi_calculator import get_kpi_calculator
from gateway.app.analytics.insights_engine import get_insights_engine
from gateway.app.analytics.event_store import get_event_store
from gateway.app.analytics.alert_manager import get_alert_manager


# =============================================================================
# Security / Config
# =============================================================================

ENV = os.getenv("ENV", "development").strip().lower()

# In local/dev you likely run Neural on 127.0.0.1:8002
# For production you can disable private/localhost via env:
#   DASHBOARD_ALLOW_PRIVATE_NEURAL=false
ALLOW_PRIVATE_NEURAL = os.getenv("DASHBOARD_ALLOW_PRIVATE_NEURAL", "true").strip().lower() in ("1", "true", "yes")

# Required for protected API calls:
#   export DASHBOARD_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY", "").strip()

# Required for chat proxy to Neural Engine internal endpoint:
NOOGH_INTERNAL_TOKEN = os.getenv("NOOGH_INTERNAL_TOKEN", "").strip()

# Neural base URL:
NEURAL_ENGINE_URL = os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002").strip()


# =============================================================================
# Simple in-memory rate limiter (no external deps)
# =============================================================================

@dataclass
class RateLimit:
    max_requests: int
    window_seconds: int


class SimpleRateLimiter:
    """
    Thread-safe simple limiter:
    - Uses per-key deque of timestamps
    - Evicts old timestamps
    """

    def __init__(self) -> None:
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: RateLimit) -> tuple[bool, int]:
        """
        Returns (allowed, remaining)
        """
        now = time.time()
        with self._lock:
            dq = self._calls[key]
            # evict old
            while dq and (now - dq[0]) > limit.window_seconds:
                dq.popleft()

            if len(dq) >= limit.max_requests:
                return (False, 0)

            dq.append(now)
            remaining = max(0, limit.max_requests - len(dq))
            return (True, remaining)


rate_limiter = SimpleRateLimiter()

RL_STATS = RateLimit(60, 60)          # 60/min
RL_KPIS = RateLimit(120, 60)         # 120/min
RL_TRENDS = RateLimit(120, 60)       # 120/min
RL_INSIGHTS = RateLimit(60, 60)      # 60/min
RL_EXPORT = RateLimit(10, 300)       # 10/5min
RL_ALERTS = RateLimit(60, 60)        # 60/min
RL_ALERTS_CLEAR = RateLimit(10, 60)  # 10/min
RL_AUTONOMIC = RateLimit(30, 60)     # 30/min
RL_CHAT = RateLimit(15, 60)          # 15/min


def _client_key(request: Request) -> str:
    """
    A sane key:
    - Prefer X-Forwarded-For first IP, else request.client.host
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        first = xff.split(",")[0].strip()
        return first or (request.client.host if request.client else "unknown")
    return request.client.host if request.client else "unknown"


def _enforce_rl(request: Request, limit: RateLimit, bucket: str) -> int:
    key = f"{bucket}:{_client_key(request)}"
    allowed, remaining = rate_limiter.allow(key, limit)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    return remaining


# =============================================================================
# Input validation
# =============================================================================

def _validate_int(name: str, value: Any) -> int:
    try:
        v = int(value)
    except Exception:
        raise HTTPException(status_code=400, detail=f"{name} must be an integer")
    return v


def validate_window_seconds(window: int) -> int:
    window = _validate_int("window", window)
    if window < 1:
        raise HTTPException(status_code=400, detail="window must be positive")
    if window > 86400:
        raise HTTPException(status_code=400, detail="window cannot exceed 86400 seconds")
    return window


def validate_buckets(buckets: int) -> int:
    buckets = _validate_int("buckets", buckets)
    if buckets < 1:
        raise HTTPException(status_code=400, detail="buckets must be positive")
    if buckets > 100:
        raise HTTPException(status_code=400, detail="buckets cannot exceed 100")
    return buckets


def _validate_int(name: str, value):
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value

def validate_limit(limit: int) -> int:
    try:
        limit = _validate_int("limit", limit)
    except TypeError as e:
        _logger.error(f"Type validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    if limit < 1:
        _logger.error(f"Invalid limit value: {limit}. Limit must be positive.")
        raise HTTPException(status_code=400, detail="limit must be positive")
    
    if limit > 1000:
        _logger.error(f"Invalid limit value: {limit}. Limit cannot exceed 1000.")
        raise HTTPException(status_code=400, detail="limit cannot exceed 1000")
    
    _logger.info(f"Validated limit: {limit}")
    return limit


def validate_interval(interval: int) -> int:
    interval = _validate_int("interval", interval)
    if interval < 1:
        raise HTTPException(status_code=400, detail="interval must be at least 1 second")
    if interval > 3600:
        raise HTTPException(status_code=400, detail="interval cannot exceed 3600 seconds")
    return interval


def validate_export_format(fmt: str) -> str:
    fmt = (fmt or "").strip().lower()
    if fmt not in ("json", "csv"):
        raise HTTPException(status_code=400, detail="fmt must be 'json' or 'csv'")
    return fmt


# =============================================================================
# Autonomic Control Proxy
# =============================================================================

@router.get("/autonomic/status")
async def autonomic_status(request: Request):
    """Proxy to neural autonomic status"""
    remaining = _enforce_rl(request, RL_STATS, "autonomic_status")
    
    neural_base = _neural_base()
    try:
        status_code, data = await _httpx_request(
            "GET",
            f"{neural_base}/api/v1/autonomic/status",
            timeout=5.0
        )
        return JSONResponse(data if status_code == 200 else {"error": "Failed to get status"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/autonomic/start")
async def autonomic_start(
    request: Request, 
    interval: int = 60,
    user: dict = Depends(require_role("operator", "admin"))
):
    """Proxy to start autonomic loop (requires operator+ role)"""
    remaining = _enforce_rl(request, RL_STATS, "autonomic_start")
    
    neural_base = _neural_base()
    try:
        status_code, data = await _httpx_request(
            "POST",
            f"{neural_base}/api/v1/autonomic/start?interval={interval}",
            timeout=5.0
        )
        return JSONResponse(data if status_code == 200 else {"error": "Failed to start"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/autonomic/stop")
async def autonomic_stop(
    request: Request,
    user: dict = Depends(require_role("operator", "admin"))
):
    """Proxy to stop autonomic loop (requires operator+ role)"""
    remaining = _enforce_rl(request, RL_STATS, "autonomic_stop")
    
    neural_base = _neural_base()
    try:
        status_code, data = await _httpx_request(
            "POST",
            f"{neural_base}/api/v1/autonomic/stop",
            timeout=5.0
        )
        return JSONResponse(data if status_code == 200 else {"error": "Failed to stop"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# =============================================================================
# Chat Proxy
# =============================================================================

def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """
    Enforce DASHBOARD_API_KEY for all dashboard APIs.
    """
    # 2. Try API Key
    if x_api_key:
        # Support multiple keys (comma-separated in env)
        valid_keys = [
            k.strip() for k in os.getenv("DASHBOARD_API_KEY", "").split(",") 
            if k.strip()
        ]
        
        if not valid_keys:
             raise HTTPException(
                status_code=500,
                detail="DASHBOARD_API_KEY is not configured on the server",
            )
            
        if x_api_key in valid_keys:
            return {"role": "developer", "type": "api_key"}
            
    # 3. Fail
    raise HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# =============================================================================
# SSRF protection for NEURAL_ENGINE_URL
# =============================================================================

def validate_neural_url(url: str) -> str:
    if not url:
        raise HTTPException(status_code=500, detail="NEURAL_ENGINE_URL is not set")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=500, detail="NEURAL_ENGINE_URL must be http or https")

    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise HTTPException(status_code=500, detail="NEURAL_ENGINE_URL has no hostname")

    # Allow localhost/private only if configured (default true for your local setup)
    if not ALLOW_PRIVATE_NEURAL:
        # Block localhost names
        if host in ("localhost",):
            raise HTTPException(status_code=500, detail="NEURAL_ENGINE_URL localhost is not allowed")
        # If host is an IP, block private/reserved ranges
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise HTTPException(status_code=500, detail="NEURAL_ENGINE_URL private/loopback IP is not allowed")
        except ValueError:
            # Not an IP; could be DNS name. In strict mode you may want DNS resolution + checks (not done here).
            pass

    # normalize: strip trailing slash
    return url.rstrip("/")


def _neural_base() -> str:
    return validate_neural_url(NEURAL_ENGINE_URL)


# =============================================================================
# HTTP helper
# =============================================================================

async def _httpx_get_json(url: str, timeout: float = 2.0) -> Optional[Dict[str, Any]]:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            if 200 <= r.status_code < 300:
                return r.json()
    except Exception:
        return None
    return None


async def _httpx_request(method: str, url: str, timeout: float = 20.0, **kwargs) -> tuple[int, Any]:
    import httpx
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method, url, **kwargs)
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, {"detail": (r.text or "").strip()}


# =============================================================================
# Output sanitization (backend)
# =============================================================================

def _sanitize_output(text: str) -> str:
    """
    Defensive sanitization:
    - Keep as plain text (preserve newlines!)
    - Remove obvious script-ish patterns
    - Fix unicode escape sequences for Arabic (safely, without unicode_escape)
    """
    if not isinstance(text, str):
        text = str(text)

    # Fix unicode escape sequences safely (only \\uXXXX, preserve \n \t etc.)
    import re as _re
    def _replace_unicode_escape(m):
        try:
            return chr(int(m.group(1), 16))
        except (ValueError, OverflowError):
            return m.group(0)
    
    if '\\u' in text:
        text = _re.sub(r'\\u([0-9a-fA-F]{4})', _replace_unicode_escape, text)

    # remove NULL bytes
    text = text.replace("\x00", "")

    # strip dangerous patterns (minimal)
    text = re.sub(r"(?is)<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text)
    text = re.sub(r"(?i)javascript:", "", text)
    text = re.sub(r"(?i)vbscript:", "", text)

    # keep as-is; preserve newlines for frontend rendering
    return text


def _clean_response_for_user(text: str) -> str:
    """
    Clean response for user display - remove internal debug info.
    
    Removes:
    - Raw JSON with thought/action/trace
    - Internal debug markers
    - Protocol violation details
    - Hallucinated Python code blocks
    - Fake decision JSON arrays
    - Markdown code fences
    
    Extracts:
    - Actual answer content
    - Arabic response text
    """
    if not isinstance(text, str):
        return str(text) if text else ""
    
    import json as json_module
    
    # If text looks like JSON, try to extract content
    text_stripped = text.strip()
    if text_stripped.startswith('{') and text_stripped.endswith('}'):
        try:
            obj = json_module.loads(text_stripped)
            
            # Priority order for extracting user-facing content
            content_keys = ['content', 'answer', 'answer_ar', 'summary_ar', 'result', 'response']
            for key in content_keys:
                if key in obj and obj[key]:
                    return str(obj[key])
            
            # If has thought but no content, use thought as fallback
            if 'thought' in obj and obj['thought']:
                return str(obj['thought'])
                
        except json_module.JSONDecodeError:
            pass
    
    # ===== STRIP HALLUCINATED CODE BLOCKS =====
    
    # Remove markdown code fences (```python ... ``` or ``` ... ```)
    text = re.sub(r'```\w*\n.*?```', '', text, flags=re.DOTALL)
    # Single-line code fences
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # Remove Python code patterns (def, class, import, print, etc.)
    python_patterns = [
        r'(?m)^#\s*(Default behavior|TODO|FIXME|NOTE).*$',     # Code comments
        r'(?m)^def\s+\w+\(.*?\):.*$',                          # Function definitions
        r'(?m)^\s+(?:return|print|raise|import|from)\s+.*$',    # Indented code
        r'(?m)^import\s+\w+.*$',                                # Top-level imports
        r'(?m)^from\s+\w+.*import.*$',                          # From imports
        r'(?m)^class\s+\w+.*:.*$',                              # Class definitions
    ]
    for pat in python_patterns:
        text = re.sub(pat, '', text)
    
    # Remove fake decision JSON arrays [ { 'decision': ..., 'action': ... } ]
    text = re.sub(r'\[\s*\{[^]]*?[\'"](?:decision|action)[\'"][^]]*?\}\s*\]', '', text, flags=re.DOTALL)
    
    # Remove inline single-quoted Python dicts/lists that look like code
    text = re.sub(r"(?m)^\s*\[\s*$", '', text)
    text = re.sub(r"(?m)^\s*\]\s*$", '', text)
    text = re.sub(r"(?m)^\s*\{\s*$", '', text)
    text = re.sub(r"(?m)^\s*\}\s*$", '', text)
    
    # Remove lines that look like variable assignment or method calls
    text = re.sub(r"(?m)^\s*\w+\.\w+\(.*?\)\s*$", '', text)      # obj.method(...)
    text = re.sub(r"(?m)^\s*\w+\s*=\s*\w+\(.*?\)\s*$", '', text)  # var = func(...)
    
    # Remove patterns that expose internal structure
    internal_patterns = [
        r'\{"thought"[^}]*\}',                    # JSON thought objects
        r'\{"action"[^}]*\}',                     # JSON action objects
        r'action:\s*\w+',                         # action: ... patterns
        r'thought:\s*[^\n]+',                     # thought: ... patterns  
        r'Final_answer',                          # Internal action type
        r'final_answer',
        r'tool_call',
        r'\[TOOL:.*?\]',                          # Tool call markers
        r'THINK:\s*',                             # ReAct protocol markers
        r'ACT:\s*',
        r'REFLECT:\s*',
        r'ANSWER:\s*',
        r'NONE\s*$',                              # ACT: NONE leftover
        r'معالجة عبر البروكسي العصبي\.?\s*',      # Internal proxy message
        # Arabic thinking markers (model-generated planning text)
        r'نوقة\s*\(\s*(?:تفكير|THINKING|thinking)\s*\)\s*:.*?(?=\n|$)',
        r'القرار(?:ات)?\s*\(\s*(?:JSON|json)\s*\)\s*:.*?(?=\n|$)',
        r'القرار(?:ات)?\s*:?\s*---.*',
        r"'\s*decision\s*'\s*:\s*'[^']*'",
        r'\{\s*\'decision\'[^}]*\}',
        r'سأقوم\s+ب[^.]+\.',
        r'سأتحقق\s+[^.]+\.',
        r'دعني\s+[^.]+\.',
        r'يجب أن يكون لي[^.]+\.',
        r'هل هناك أي شيء[^?؟]+[?؟]',
    ]
    
    for pattern in internal_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


def _preprocess_message(text: str) -> str:
    """
    معالجة مسبقة للرسائل قبل إرسالها إلى Neural Engine
    Preprocess messages before sending to Neural Engine
    """
    if not isinstance(text, str):
        return str(text) if text else ""

    # تصحيح الأخطاء الشائعة في اسم NOOGH — فقط العربية
    # ⚠️ لا نحوّل "noogh" الإنجليزية لأنها تكسر مسارات الملفات مثل /home/noogh/
    arabic_corrections = [
        ("نعوذ", "نووغ"),
        ("نوغه", "نووغ"),
    ]
    
    for wrong, correct in arabic_corrections:
        if wrong in text:
            text = text.replace(wrong, correct)
            logger.info(f"Input correction: '{wrong}' → '{correct}'")

    # ⚠️ لا نحوّل × إلى * هنا — react_loop يتعامل معها بنفسه
    # التحويل هنا كان يفعّل SafeMath بالخطأ على أسئلة عربية

    return text


# =============================================================================
# API: Stats + Analytics + Alerts + Autonomic + Chat
# =============================================================================

@router.get("/stats")
async def dashboard_stats(request: Request):
    remaining = _enforce_rl(request, RL_STATS, "stats")

    store = get_event_store()
    alerts = get_alert_manager()

    neural_base = _neural_base()
    start = time.time()
    health = await _httpx_get_json(f"{neural_base}/health", timeout=2.0)
    latency_ms = round((time.time() - start) * 1000.0, 2)

    neural_status = "online" if health else "offline"
    
    # جمع إحصائيات النظام باستخدام psutil
    system_stats = {}
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count()
        
        memory = psutil.virtual_memory()
        mem_total = memory.total / (1024**3)  # GB
        mem_used = memory.used / (1024**3)    # GB
        mem_percent = memory.percent
        
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024**3)   # GB
        disk_used = disk.used / (1024**3)     # GB
        disk_percent = disk.percent
        
        system_stats = {
            "cpu": {
                "usage_percent": round(cpu_percent, 1),
                "cores": cpu_cores
            },
            "memory": {
                "total_gb": round(mem_total, 2),
                "used_gb": round(mem_used, 2),
                "percent": round(mem_percent, 1)
            },
            "disk": {
                "total_gb": round(disk_total, 2),
                "used_gb": round(disk_used, 2),
                "percent": round(disk_percent, 1)
            }
        }
    except Exception as e:
        logger.warning(f"Failed to get system stats: {e}")
        system_stats = {"error": str(e)}

    payload: Dict[str, Any] = {
        "neural": {
            "status": neural_status,
            "latency_ms": latency_ms if health else None,
        },
        "system": system_stats,
        "store": store.stats(),
        "alerts": {"count": len(alerts.list_alerts(limit=1000))},
        "ts": time.time(),
        "rate_limit_remaining": remaining,
    }

    # only show base in non-production (avoid leaking internals)
    if ENV != "production":
        payload["neural"]["base"] = neural_base

    return JSONResponse(payload)


@router.get("/analytics/kpis")
def get_kpis(request: Request, window: int = 3600):
    _enforce_rl(request, RL_KPIS, "kpis")
    window = validate_window_seconds(window)
    kpi_calc = get_kpi_calculator()
    data = kpi_calc.calculate_all(window_seconds=window)
    return JSONResponse(data)


@router.get("/analytics/insights")
def get_insights(request: Request, window: int = 3600):
    _enforce_rl(request, RL_INSIGHTS, "insights")
    window = validate_window_seconds(window)

    kpi_calc = get_kpi_calculator()
    insights_engine = get_insights_engine(kpi_calc)
    insights = insights_engine.analyze(window_seconds=window)

    return JSONResponse({
        "window_seconds": window,
        "count": len(insights),
        "insights": [i.to_dict() for i in insights],
    })


@router.get("/analytics/trends")
def get_trends(request: Request, window: int = 3600, buckets: int = 12):
    _enforce_rl(request, RL_TRENDS, "trends")
    window = validate_window_seconds(window)
    buckets = validate_buckets(buckets)

    store = get_event_store()
    data = store.bucketize_counts(window_seconds=window, buckets=buckets)
    return JSONResponse(data)


@router.get("/analytics/export")
def export_analytics(request: Request, window: int = 3600, fmt: str = "json"):
    _enforce_rl(request, RL_EXPORT, "export")
    window = validate_window_seconds(window)
    fmt = validate_export_format(fmt)

    store = get_event_store()

    if fmt == "csv":
        csv_data = store.export_csv(window_seconds=window)
        return Response(
            content=csv_data,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=events.csv",
                "X-Content-Type-Options": "nosniff",
            },
        )

    json_data = store.export_json(window_seconds=window)
    return Response(
        content=json_data,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=events.json",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/alerts/history")
def alerts_history(request: Request, limit: int = 200):
    _enforce_rl(request, RL_ALERTS, "alerts_history")
    limit = validate_limit(limit)
    mgr = get_alert_manager()
    return JSONResponse({"success": True, "alerts": mgr.list_alerts(limit=limit)})


@router.post("/alerts/clear")
def alerts_clear(
    request: Request,
    user: dict = Depends(require_role("admin"))
):
    """Clear all alerts (admin-only)"""
    _enforce_rl(request, RL_ALERTS_CLEAR, "alerts_clear")
    mgr = get_alert_manager()
    mgr.clear_alerts()
    return JSONResponse({"success": True})


@router.post("/autonomic/start")
async def autonomic_start_v2(
    request: Request, 
    interval: int = 10,
    user: dict = Depends(require_role("operator", "admin"))
):
    """Start autonomic loop (operator+, duplicate endpoint for compatibility)"""
    _enforce_rl(request, RL_AUTONOMIC, "autonomic_start")
    interval = validate_interval(interval)

    neural_base = _neural_base()
    try:
        status_code, data = await _httpx_request(
            "POST",
            f"{neural_base}/api/v1/autonomic/start",
            timeout=20.0,
            params={"interval": interval},
        )
        return JSONResponse(data, status_code=status_code)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=502)


@router.post("/autonomic/stop")
async def autonomic_stop_v2(
    request: Request,
    user: dict = Depends(require_role("operator", "admin"))
):
    """Stop autonomic loop (operator+, duplicate endpoint for compatibility)"""
    _enforce_rl(request, RL_AUTONOMIC, "autonomic_stop")
    neural_base = _neural_base()
    try:
        status_code, data = await _httpx_request(
            "POST",
            f"{neural_base}/api/v1/autonomic/stop",
            timeout=20.0,
        )
        return JSONResponse(data, status_code=status_code)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=502)


@router.get("/autonomic/status")
async def autonomic_status(request: Request):
    _enforce_rl(request, RL_AUTONOMIC, "autonomic_status")
    neural_base = _neural_base()
    try:
        status_code, data = await _httpx_request(
            "GET",
            f"{neural_base}/api/v1/autonomic/status",
            timeout=20.0,
        )
        return JSONResponse(data, status_code=status_code)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=502)


async def verify_chat_access(
    request: Request,
    x_api_key: str = Header(None, alias="X-API-Key"),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> dict:
    """
    Flexible authentication for chat:
    0. Allow localhost access without auth (for development)
    1. Try JWT Token (standard user auth)
    2. Try API Key (dev/headless auth)
    """
    # 0. Localhost bypass for development
    client_host = request.client.host if request.client else ""
    if client_host in ("127.0.0.1", "localhost", "::1"):
        return {"username": "localhost_user", "role": "admin", "type": "localhost"}
    
    # 1. Try JWT
    if auth:
        try:
            return await verify_gateway_token(auth)
        except HTTPException:
            pass # Fallthrough to API key check
            
    # 2. Try API Key
    if x_api_key:
        try:
            valid_key = verify_api_key(x_api_key)
            return {"username": "apikey_user", "role": "admin", "type": "apikey"}
        except HTTPException:
            pass

    # 3. Fail
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Please login or provide API Key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# =============================================================================
# Auth Endpoints
# =============================================================================

@router.post("/auth/login")
async def login(request: Request):
    """Exchange API Key for Session Token"""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    api_key = data.get("api_key") or data.get("password")
    
    # Verify API Key
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key required")
        
    # Check against config
    valid_keys = [k.strip() for k in DASHBOARD_API_KEY.split(",") if k.strip()]
    if api_key not in valid_keys:
        # 1s delay to prevent brute force
        time.sleep(1)
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # Generate Token
    # Use JWT_SECRET_KEY which we just aligned in .env
    secret = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_PLEASE")
    now = time.time()
    payload = {
        "sub": "admin",
        "role": "admin",
        "iat": now,
        "exp": now + 86400 * 7  # 7 days
    }
    
    import jwt
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    if isinstance(token, bytes):
        token = token.decode('utf-8')
        
    return JSONResponse({"token": token, "type": "bearer"})


@router.post("/chat/proxy")
async def chat_proxy(
    request: Request,
    user: dict = Depends(verify_chat_access)
):
    """
    Chat proxy with agent orchestration support
    - Detects agent intent in user messages
    - Routes to orchestrator if agent needed
    - Falls back to Neural Engine for general chat
    """
    remaining = _enforce_rl(request, RL_CHAT, "chat")

    if not NOOGH_INTERNAL_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="NOOGH_INTERNAL_TOKEN is not configured on the server",
        )

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="No message provided")
    if len(message) > 5000:
        raise HTTPException(status_code=400, detail="Message too long (max 5000 chars)")

    # Phase 2: Agent Intent Detection
    from gateway.app.api.chat_bridge import detect_agent_intent, invoke_agent_from_chat
    
    agent_intent = detect_agent_intent(message)
    
    if agent_intent:
        # Agent capability detected - invoke orchestrator
        logger.info(f"Agent intent detected: {agent_intent['agent_type']}")
        
        try:
            agent_response = await invoke_agent_from_chat(
                intent=agent_intent,
                user_token=request.headers.get("authorization", "").replace("Bearer ", "")
            )
            
            return JSONResponse({
                "success": True,
                "message": agent_response.get("response"),
                "agent": agent_response.get("agent"),
                "mode": "agent"
            })
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            # Fallback to Neural Engine on agent error
            pass

    # Default: Neural Engine chat
    neural_base = _neural_base()
    validate_neural_url(neural_base)

    # معالجة مسبقة للرسالة - تصحيح الإدخال والرموز
    message = _preprocess_message(message)

    neural_base = _neural_base()

    # ========== استخدام NOOGHCore كمحرك أساسي ==========
    # DISABLED: NOOGHCore temporarily disabled due to missing tool_registry module
    # This will be re-enabled once the tool registry system is properly set up
    # try:
    #     from neural_engine.tools.noogh_core import NOOGHCore
    #     
    #     noogh_core = NOOGHCore()
    #     noogh_core.thinking_mode = True
    #     
    #     # NOOGHCore يحدد بنفسه إذا كان السؤال يحتاج أدوات نظام أو ReAct
    #     result = noogh_core.process_query(message)
    #     
    #     # إذا أرجع None = السؤال يحتاج ReAct (حساب/شرح/مفاهيم)
    #     if result is not None and len(result) > 50:
    #         resp_text = _sanitize_output(result)
    #         resp_text += "\n\n---\n🔧 **المصدر:** أدوات NOOGH الحقيقية"
    #         
    #         return JSONResponse(
    #             {"response": resp_text, "remaining_per_min": remaining},
    #             status_code=200,
    #         )
    #     # None أو نتيجة فارغة = نذهب إلى ReAct
    # except Exception as noogh_err:
    #     logger.warning(f"NOOGHCore failed, falling back to ReAct: {noogh_err}")
    
    # ========== GATEWAY-LEVEL COGNITIVE INTERCEPTION ==========
    _cognitive_intercepted = False
    _cognitive_resp = None
    _msg = message.strip()
    
    if _msg.startswith("لماذا ") or _msg.startswith("ليش ") or _msg.startswith("why "):
        try:
            from unified_core.intelligence import ActiveQuestioner
            logger.info("Cognitive Intecept: ActiveQuestioner triggered")
            q = ActiveQuestioner(max_depth=3)
            res = q.ask_why_chain(_msg)
            
            _cognitive_resp = (
                f"🧠 **التحليل الإدراكي العميق (Active Questioning):**\n\n"
                f"**السبب الجذري المستنتج:**\n{res['root_cause']}\n\n"
                f"---\n*تم الوصول إلى هذا الاستنتاج بعد الغوص لعمق {res['depth_reached']} مستويات تحليلية.*"
            )
            _cognitive_intercepted = True
        except Exception as e:
            logger.error(f"Cognitive Intercept Error (Why): {e}")

    elif " ادعاء " in _msg or _msg.endswith("سيهبط") or _msg.endswith("سينهار") or _msg.endswith("سيرتفع"):
        try:
            from unified_core.intelligence import CriticalThinker, Evidence
            logger.info("Cognitive Intecept: CriticalThinker triggered")
            t = CriticalThinker()
            
            issues_found = t._call_neural_engine_eval(
                claim=_msg, 
                evidence_text="طُلِب تقييم هذا الادعاء بشكل مفاجئ من المستخدم.", 
                reasoning="بدون حيثيات واضحة مقدمة من المستخدم."
            )
            
            if not issues_found:
                _cognitive_resp = f"🛡️ **تقييم التفكير النقدي:**\nهذا الادعاء سليم مبدئياً ولا توجد فيه مغالطات واضحة."
            else:
                issues_formatted = "\n".join([f"- {iss}" for iss in issues_found])
                _cognitive_resp = (
                    f"❌ **VETO - تقييم التفكير النقدي:**\n"
                    f"أرفض هذا الادعاء لوجود المغالطات أو الانحيازات التالية:\n\n{issues_formatted}\n\n"
                    f"---\n*تم فحص هذا الادعاء عبر محرك CriticalThinker السيادي.*"
                )
            _cognitive_intercepted = True
        except Exception as e:
            logger.error(f"Cognitive Intercept Error (Claim): {e}")

    if _cognitive_intercepted and _cognitive_resp:
        return JSONResponse({
            "status": "success",
            "response": _cognitive_resp,
            "remaining_requests": remaining,
            "mode": "cognitive"
        })

    # ========== GATEWAY-LEVEL COMMAND INTERCEPTION ==========
    # For known command patterns, execute directly without waiting for the 7B model.
    import re as _ire
    import subprocess as _sp
    
    _intercepted = False
    _cmd = None
    _msg = message.strip()
    
    # Pattern Group 1: Directory listing
    # "اعرض محتويات المجلد /path" / "اعرض محتويات /path" / "شوف /path"
    _m = _ire.search(r'(?:اعرض|عرض|أظهر|شوف|وريني|افتح|عرضلي|اظهر)\s+(?:لي\s+)?(?:محتويات\s+)?(?:المجلد\s+|المسار\s+|الدليل\s+|الفولدر\s+)?(/[^\s،,.؟?]+)', _msg)
    if _m:
        _cmd = f"ls -la {_m.group(1).rstrip('.,')}"
        _intercepted = True
    
    # Pattern Group 2: Read file
    # "اقرأ ملف /path" / "اقرا ملف /path" / "أرني محتوى /path"
    if not _intercepted:
        _m = _ire.search(r'(?:اقرأ|اقرا|أرني|ارني|اعرض|افتح)\s+(?:لي\s+)?(?:ملف|محتوى|محتويات\s+ملف|الملف)\s+(/[^\s،,.؟?]+)', _msg)
        if _m:
            _cmd = f"cat {_m.group(1).rstrip('.,')}"
            _intercepted = True
    
    # Pattern Group 3: Execute safe command
    # "نفذ الأمر ls -la" / "شغل uptime" / "execute df -h"
    if not _intercepted:
        _m = _ire.search(r'(?:نفذ|شغل|شغّل|execute|run)\s+(?:الأمر\s+|الامر\s+|امر\s+)?(.+)', _msg, _ire.IGNORECASE)
        if _m:
            _raw_cmd = _m.group(1).strip().rstrip('.,')
            _safe_cmds = {"ls", "cat", "head", "tail", "wc", "find", "df", "du",
                         "uname", "hostname", "whoami", "date", "uptime", "free",
                         "pwd", "echo", "file", "stat", "tree", "which", "env",
                         "printenv", "ps", "top", "id", "groups", "lsblk",
                         "lscpu", "lsusb", "ip", "ifconfig", "ping", "dig",
                         "nslookup", "systemctl", "journalctl", "nvidia-smi"}
            _cmd_base = _raw_cmd.split()[0] if _raw_cmd.split() else ""
            if _cmd_base in _safe_cmds:
                _cmd = _raw_cmd
                _intercepted = True
    
    # Pattern Group 4: Count files
    # "كم ملف في /path" / "عدد الملفات في /path"
    if not _intercepted:
        _m = _ire.search(r'(?:كم|عدد)\s+(?:ملف|مجلد|عنصر|الملفات|المجلدات)\s+(?:في|ب|داخل|تحت)\s+(/[^\s،,.؟?]+)', _msg)
        if _m:
            _cmd = f"ls -la {_m.group(1).rstrip('.,')}"
            _intercepted = True
    
    # Pattern Group 5: System info queries
    # "ما هو اسم الجهاز" / "معلومات النظام"
    if not _intercepted:
        if _ire.search(r'(?:اسم\s+الجهاز|hostname|اسم\s+المضيف)', _msg):
            _cmd = "hostname"
            _intercepted = True
        elif _ire.search(r'(?:معلومات\s+النظام|system\s+info|uname)', _msg, _ire.IGNORECASE):
            _cmd = "uname -a"
            _intercepted = True
        elif _ire.search(r'(?:مساحة\s+القرص|المساحة|disk\s+space|حجم\s+القرص)', _msg, _ire.IGNORECASE):
            _cmd = "df -h"
            _intercepted = True
        elif _ire.search(r'(?:الذاكرة|الرام|memory|ram)', _msg, _ire.IGNORECASE):
            _cmd = "free -h"
            _intercepted = True
        elif _ire.search(r'(?:من\s+أنا|whoami|المستخدم\s+الحالي)', _msg, _ire.IGNORECASE):
            _cmd = "whoami"
            _intercepted = True
    
    # Execute intercepted command
    if _intercepted and _cmd:
        logger.info(f"Gateway intercept: '{_cmd}' for: {_msg[:60]}")
        try:
            _proc = _sp.run(
                _cmd, shell=True, capture_output=True, text=True, timeout=15,
                cwd="/home/noogh/projects/noogh_unified_system/src"
            )
            _output = _proc.stdout.strip() or _proc.stderr.strip() or "(empty)"
            if len(_output) > 4000:
                _output = _output[:4000] + "\n... [truncated]"
            
            _resp = _output + f"\n\n---\n🔧 **تنفيذ مباشر:** `{_cmd}`"
            
            return JSONResponse({
                "status": "success",
                "response": _resp,
                "remaining_requests": remaining,
                "tool_calls": [{"tool": "sys.execute", "args": {"command": _cmd}}],
                "iterations": 0
            })
        except _sp.TimeoutExpired:
            return JSONResponse({
                "status": "success",
                "response": "انتهت مهلة تنفيذ الأمر (15 ثانية)",
                "remaining_requests": remaining,
            })
        except Exception as _exec_err:
            logger.error(f"Gateway intercept error: {_exec_err}")
            pass  # Fall through to LLM
    
    # ========== CONVERSATIONAL INTENT DETECTION ==========
    # Route conversational messages through simple /process (no tools)
    # Only system commands and file operations go to ReAct
    import re as _cire
    _needs_tools = False
    _ml = _msg.lower()
    
    # Patterns that NEED tools (system commands, file ops, etc.)
    _tool_patterns = [
        r'(?:اعرض|عرض|أظهر|شوف|وريني|افتح).*(?:مجلد|ملف|محتو|مسار)',
        r'(?:اقرأ|اقرا|أرني|ارني).*(?:ملف|محتو)',
        r'(?:نفذ|شغل|شغّل|execute|run)\s+',
        r'(?:اكتب|أنشئ|انشئ).*(?:ملف|سكريبت)',
        r'(?:كم|عدد)\s+(?:ملف|مجلد|عنصر)',
        r'(?:حالة|حال)\s+(?:النظام|الخادم|السيرفر|الجهاز|الخدم)',
        r'(?:ابحث|بحث)\s+(?:عن|في)',
        r'(?:مساحة|حجم)\s+(?:القرص|الذاكرة|الرام)',
        r'(?:معلومات)\s+(?:النظام)',
        r'/(?:home|tmp|etc|var|usr|opt)/',  # File paths in message
    ]
    
    for _tp in _tool_patterns:
        if _cire.search(_tp, _msg, _cire.IGNORECASE):
            _needs_tools = True
            break
    
    # ========== Route based on intent ==========
    if _needs_tools:
        # System/file commands → ReAct with tools
        logger.info(f"Intent: TOOL_REQUIRED → ReAct path")
        try:
            status_code, data = await _httpx_request(
                "POST",
                f"{neural_base}/api/v1/process/react",
                timeout=90.0,
                json={
                    "text": message,
                    "use_react": True,
                    "store_memory": True
                },
                headers={"X-Internal-Token": NOOGH_INTERNAL_TOKEN},
            )
        except Exception as e:
            logger.error(f"Neural ReAct request failed: {e}")
            raise HTTPException(status_code=502, detail=f"Neural request failed: {e}")
    else:
        # Conversational/knowledge → simple process (no tools)
        logger.info(f"Intent: CONVERSATIONAL → simple process path")
        try:
            status_code, data = await _httpx_request(
                "POST",
                f"{neural_base}/api/v1/process",
                timeout=60.0,
                json={"text": message},
                headers={"X-Internal-Token": NOOGH_INTERNAL_TOKEN},
            )
        except Exception as e:
            logger.error(f"Neural process request failed: {e}")
            status_code = 502
            data = None

    if status_code != 200:
        # Fallback to regular process if ReAct fails
        logger.warning(f"ReAct failed with {status_code}, trying regular process")
        try:
            status_code, data = await _httpx_request(
                "POST",
                f"{neural_base}/api/v1/process",
                timeout=60.0,
                json={"text": message},
                headers={"X-Internal-Token": NOOGH_INTERNAL_TOKEN},
            )
        except Exception as e:
            logger.warning(f"Neural fallback also failed: {e}")
            status_code = 502
            data = None
        
    if status_code != 200:
        logger.error(f"All Neural endpoints failed. Last status: {status_code}")
        # Try to salvage partial response if available
        if data and ("answer" in data or "result" in data):
             pass # Continue to processing
        else:
            # ═══ OLLAMA DIRECT FALLBACK ═══
            # Neural Engine is down — talk to ollama directly
            logger.warning("Neural Engine unavailable — falling back to ollama direct")
            try:
                import httpx
                _ollama_url = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
                _ollama_model = os.getenv("VLLM_MODEL_NAME", "qwen2.5-coder:7b")
                
                _system_prompt = (
                    "أنت نظام NOOGH — نظام ذكي مستقل. أجب بالعربية بشكل مختصر ومفيد. "
                    "أنت تعمل على خادم Linux مع GPU RTX 5070."
                )
                
                async with httpx.AsyncClient(timeout=60.0) as _oclient:
                    _oresp = await _oclient.post(
                        f"{_ollama_url}/api/generate",
                        json={
                            "model": _ollama_model,
                            "prompt": message,
                            "system": _system_prompt,
                            "stream": False,
                            "options": {"temperature": 0.7, "num_predict": 512}
                        }
                    )
                    
                if _oresp.status_code == 200:
                    _odata = _oresp.json()
                    _ollama_text = _odata.get("response", "")
                    if _ollama_text:
                        return JSONResponse({
                            "status": "success",
                            "response": _ollama_text,
                            "remaining_requests": remaining,
                            "mode": "ollama_fallback"
                        })
            except Exception as _oe:
                logger.error(f"Ollama fallback also failed: {_oe}")
            
            raise HTTPException(status_code=502, detail="Neural processing failed (all backends)")
    
    # Normalize response for Frontend (frontend expects 'response' key)
    if data:
        if "answer" in data and "response" not in data:
            data["response"] = data["answer"]
        if "result" in data and "response" not in data:
            data["response"] = data["result"]
            
    # Continue to existing processing...
    
    
    resp_text = str(data.get("response", data.get("text", data.get("conclusion", data.get("answer", "FIXED_RESPONSE")))))
    resp_text = _sanitize_output(resp_text)
    observations = data.get("observations", [])
    tool_calls = data.get("tool_calls", [])
    iterations = data.get("iterations", 0)
    
    # If answer is raw JSON (contains thought/action), use observations instead
    if resp_text and ('{"thought"' in resp_text or '{"action"' in resp_text or '"actions"' in resp_text):
        # Answer is raw JSON - use observations if available
        if observations:
            result_parts = ["### 📊 النتائج:\n"]
            for i, obs in enumerate(observations, 1):
                clean_obs = str(obs).strip()[:4000]
                if len(observations) > 1:
                    result_parts.append(f"**{i}.** {clean_obs}\n")
                else:
                    result_parts.append(clean_obs)
            resp_text = "\n".join(result_parts)
        else:
            # No observations - extract thought as fallback
            import re
            thought_match = re.search(r'"thought"\s*:\s*"([^"]*)"', resp_text)
            if thought_match:
                resp_text = thought_match.group(1).replace('\\n', '\n')
    
    # If answer still empty but we have observations, use them
    if (not resp_text or len(resp_text.strip()) < 20) and observations:
        result_parts = ["### 📊 النتائج:\n"]
        for i, obs in enumerate(observations, 1):
            clean_obs = str(obs).strip()[:4000]
            if len(observations) > 1:
                result_parts.append(f"**{i}.** {clean_obs}\n")
            else:
                result_parts.append(clean_obs)
        resp_text = "\n".join(result_parts)
    
    # Add tool info footer
    if tool_calls:
        tool_info = f"\n\n---\n🔧 **الأدوات المستخدمة:** {len(tool_calls)} | **التكرارات:** {iterations}"
        resp_text = resp_text + tool_info if resp_text else tool_info

    resp_text = _sanitize_output(resp_text)

    # Fallback: إذا فشل النموذج في الحساب الرياضي، نحسبه محلياً
    if "FAILURE" in resp_text or "unintelligible" in resp_text or not resp_text.strip():
        import re
        # Check if it's a math request
        math_expr = re.findall(r'[\d\.]+[\s]*[\+\-\*\/\×\÷][\s]*[\d\.]+(?:[\s]*[\+\-\*\/\×\÷][\s]*[\d\.]+)*', message)
        if math_expr:
            try:
                expr = math_expr[0]
                original_expr = expr
                expr = expr.replace('×', '*').replace('÷', '/')
                
                # Physical-Hardening v2.4.9: Safe math evaluation using ast
                import ast
                import operator
                
                ops = {
                    ast.Add: operator.add, ast.Sub: operator.sub, 
                    ast.Mult: operator.mul, ast.Div: operator.truediv,
                    ast.Pow: operator.pow, ast.BitXor: operator.xor,
                    ast.USub: operator.neg
                }
                
                def _safe_eval(node):
                    if isinstance(node, ast.Constant): return node.value
                    if isinstance(node, (ast.Num, ast.Str)): return getattr(node, 'n', getattr(node, 's', None))
                    if isinstance(node, ast.BinOp):
                        return ops[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
                    if isinstance(node, ast.UnaryOp):
                        return ops[type(node.op)](_safe_eval(node.operand))
                    raise TypeError(f"Unsafe node: {node}")

                node = ast.parse(expr, mode='eval').body
                result_value = _safe_eval(node)
                
                resp_text = f"""### الحساب الرياضي الذاتي 🧮

**العملية:** {original_expr}

**أمان المعالجة:** تم استخدام المحلل الهيكلي (Safe AST Parser)

**النتيجة:** {result_value}"""
            except Exception:
                pass  # Keep original failure message

    # Final cleanup: remove internal debug markers + handle code fences (minimal)
    import re as _re
    # Remove ReAct protocol markers and thinking markers
    for pat in [
        r'THINK:\s*', r'ACT:\s*', r'REFLECT:\s*', r'ANSWER:\s*',
        r'NONE\s*$',
        r'<\|im_.*?\|>',
    ]:
        resp_text = _re.sub(pat, '', resp_text, flags=_re.IGNORECASE)
    
    # Handle markdown code fences: strip ``` markers but KEEP content
    resp_text = _re.sub(r'```\w*\n', '', resp_text)  # Opening ```python\n
    resp_text = _re.sub(r'\n```', '', resp_text)       # Closing \n```
    resp_text = _re.sub(r'```', '', resp_text)          # Any remaining ```
    
    resp_text = resp_text.strip()

    return JSONResponse({
        "status": "success",
        "response": resp_text,
        "remaining_requests": remaining,
        "engine": "react" if data.get("tool_calls") else "reasoning"
    })


# =============================================================================
# Dashboard UI (CSP + security headers)
# =============================================================================

def _security_headers(nonce: str) -> Dict[str, str]:
    csp = [
        "default-src 'self'",
        # allow CDN (bootstrap/chartjs). inline script/style allowed only via nonce
        f"script-src 'self' https://cdn.jsdelivr.net 'nonce-{nonce}' 'unsafe-inline'",
        "script-src-attr 'unsafe-inline'",
        f"style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com 'unsafe-inline'",
        "style-src-attr 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com data:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ]
    headers = {
        "Content-Security-Policy": "; ".join(csp),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
        "Cache-Control": "no-store",
    }
    # HSTS only if you're actually serving HTTPS behind a proxy
    if os.getenv("DASHBOARD_ENABLE_HSTS", "false").strip().lower() in ("1", "true", "yes"):
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


@public_router.get("/dashboard", response_class=HTMLResponse)
def dashboard_ui():
    nonce = secrets.token_hex(16)
    return HTMLResponse(content=_get_safe_html(nonce), headers=_security_headers(nonce))


def _get_safe_html(nonce: str) -> str:
    """
    Modern dashboard UI:
    - Uses X-API-Key stored in localStorage
    - Escapes any text inserted via templates
    - Chat messages rendered safely
    """
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>نوقة | السيادة الرقمية</title>

  <!-- Fonts & Core -->
  <script src="https://cdn.tailwindcss.com" nonce="{nonce}"></script>
  <link nonce="{nonce}" rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Noto+Sans+Arabic:wght@300;400;600;700&display=swap">
  <link nonce="{nonce}" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
  
  <script nonce="{nonce}">
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              50: '#f0f4ff', 100: '#d9e2ff', 200: '#b8c9ff', 300: '#8ca1ff',
              400: '#5c73ff', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8',
              800: '#1e40af', 900: '#1e3a8a', 950: '#0a0c10',
            }},
            sovereign: {{
              red: '#dc2626', orange: '#ea580c', gold: '#fbbf24'
            }}
          }},
          fontFamily: {{
            sans: ['Outfit', 'Noto Sans Arabic', 'sans-serif'],
            mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
          }},
        }}
      }}
    }}
  </script>

  <style nonce="{nonce}">
    :root {{ scroll-behavior: smooth; }}
    body {{ background-color: #0a0c10; color: #e2e8f0; font-family: 'Outfit', 'Noto Sans Arabic', sans-serif; }}
    
    .glass {{ background: rgba(13, 17, 23, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); }}
    .glass-card {{ background: rgba(13, 17, 23, 0.4); border: 1px solid rgba(255,255,255,0.05); transition: all 0.3s ease; }}
    .glass-card:hover {{ border-color: rgba(59, 130, 246, 0.3); transform: translateY(-2px); }}
    
    .status-pulse {{ width: 8px; height: 8px; border-radius: 50%; position: relative; }}
    .status-pulse::after {{
      content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      border-radius: 50%; animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
      background: inherit; opacity: 0.6;
    }}
    @keyframes pulse {{ 0%, 100% {{ transform: scale(1); opacity: 0.6; }} 50% {{ transform: scale(2.5); opacity: 0; }} }}
    
    .scroll-dark::-webkit-scrollbar {{ width: 4px; }}
    .scroll-dark::-webkit-scrollbar-track {{ background: transparent; }}
    .scroll-dark::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 10px; }}
    .scroll-dark::-webkit-scrollbar-thumb:hover {{ background: rgba(59, 130, 246, 0.5); }}

    .thought-block {{ border-right: 2px solid rgba(59, 130, 246, 0.3); background: rgba(255,255,255,0.02); }}
    .animate-entry {{ animation: entry 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }}
    @keyframes entry {{ from {{ opacity: 0; transform: translateY(10px) scale(0.98); }} to {{ opacity: 1; transform: translateY(0) scale(1); }} }}
  </style>
</head>
<body class="min-h-screen Selection:bg-brand-500/30">

  <!-- Background Decorative Elements -->
  <div class="fixed inset-0 overflow-hidden pointer-events-none z-0">
    <div class="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-brand-500/5 blur-[120px] rounded-full"></div>
    <div class="absolute top-[40%] -right-[10%] w-[35%] h-[35%] bg-purple-500/5 blur-[120px] rounded-full"></div>
  </div>

  <div class="relative z-10 flex h-screen overflow-hidden">
    
    <!-- Sidebar Navigation -->
    <aside class="w-20 lg:w-64 glass border-l border-white/5 flex flex-col items-center lg:items-stretch py-6 px-4">
      <div class="flex items-center gap-3 mb-12 px-2">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20">
          <i class="bi bi-cpu-fill text-white fs-5"></i>
        </div>
        <div class="hidden lg:block">
          <h1 class="font-bold text-lg tracking-tight">نوقة</h1>
          <p class="text-[10px] text-slate-500 font-mono tracking-widest uppercase">Sovereign Intelligence</p>
        </div>
      </div>

      <nav class="flex-1 space-y-2">
        <button onclick="switchTab('analytics')" class="nav-item w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group scale-active bg-white/10 text-brand-400" id="btn-analytics">
          <i class="bi bi-grid-1x2"></i>
          <span class="hidden lg:block font-medium">التحليلات</span>
        </button>
        <button onclick="switchTab('chat')" class="nav-item w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group" id="btn-chat">
          <i class="bi bi-chat-dots"></i>
          <span class="hidden lg:block font-medium">الدردشة</span>
        </button>
        <button onclick="switchTab('alerts')" class="nav-item w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group" id="btn-alerts">
          <i class="bi bi-bell"></i>
          <span class="hidden lg:block font-medium">التنبيهات</span>
        </button>
        <button onclick="switchTab('control')" class="nav-item w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group" id="btn-control">
          <i class="bi bi-sliders2"></i>
          <span class="hidden lg:block font-medium">التحكم</span>
        </button>
      </nav>

      <div class="pt-6 border-t border-white/5 space-y-4">
        <button onclick="promptForLogin()" class="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-all text-sm">
          <i class="bi bi-fingerprint"></i>
          <span class="hidden lg:block">المصادقة</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col overflow-hidden">
      
      <!-- Top Header -->
      <header class="h-20 glass flex items-center justify-between px-8 border-b border-white/5">
        <div class="flex items-center gap-6">
          <div class="flex items-center gap-2">
            <div class="status-pulse bg-green-500" id="neuralPulse"></div>
            <span class="text-sm font-semibold" id="neuralText">جاري الفحص...</span>
          </div>
          <div class="h-4 w-[1px] bg-white/10 hidden md:block"></div>
          <div class="hidden md:flex items-center gap-4 text-xs text-slate-500 font-mono">
             <span id="currentTime">--:--</span>
             <span id="latencyText">RTT: --ms</span>
          </div>
        </div>

        <div class="flex items-center gap-4">
           <div class="hidden lg:flex flex-col items-end">
              <span class="text-sm font-bold text-white">المسؤول السيادي</span>
              <span class="text-[10px] text-slate-500 font-mono">ID: 0x9AF...F52</span>
           </div>
           <div class="w-10 h-10 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center">
              <i class="bi bi-person text-slate-400"></i>
           </div>
        </div>
      </header>

      <!-- View Containers -->
      <div class="flex-1 overflow-y-auto p-8 scroll-dark">

        <!-- Tab: Analytics -->
        <section id="view-analytics" class="space-y-8 animate-entry">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="glass-card p-6 rounded-2xl relative overflow-hidden group">
               <div class="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity">
                 <i class="bi bi-cpu text-8xl"></i>
               </div>
               <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">حالة النواة</p>
               <h3 class="text-2xl font-bold mb-1" id="statNeural">--</h3>
               <p class="text-[10px] mono text-slate-600" id="statNeuralMeta">0.0.0.0:8002</p>
            </div>
            <div class="glass-card p-6 rounded-2xl relative overflow-hidden group">
               <div class="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity">
                 <i class="bi bi-database text-8xl"></i>
               </div>
               <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">معدل الأحداث</p>
               <h3 class="text-2xl font-bold mb-1" id="statEvents">0</h3>
               <p class="text-[10px] mono text-slate-600">Total stored records</p>
            </div>
            <div class="glass-card p-6 rounded-2xl relative overflow-hidden group">
               <div class="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity">
                 <i class="bi bi-shield-check text-8xl"></i>
               </div>
               <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">التنبيهات النشطة</p>
               <h3 class="text-2xl font-bold mb-1 text-orange-500" id="statAlerts">0</h3>
               <p class="text-[10px] mono text-slate-600">Real-time risk monitor</p>
            </div>
            <div class="glass-card p-6 rounded-2xl relative overflow-hidden group">
               <div class="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity">
                 <i class="bi bi-activity text-8xl"></i>
               </div>
               <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">النظام الذاتي</p>
               <h3 class="text-2xl font-bold mb-1" id="statAutonomic">--</h3>
               <p class="text-[10px] mono text-slate-600" id="statAutonomicMeta">Control Loop Status</p>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 glass-card p-8 rounded-3xl">
               <div class="flex justify-between items-center mb-8">
                  <h4 class="font-bold flex items-center gap-3">
                    <i class="bi bi-bar-chart text-brand-500"></i>
                    تحليل تدفق البيانات (Trends)
                  </h4>
                  <div class="flex bg-brand-950 p-1 rounded-lg border border-white/5">
                    <span class="px-3 py-1 text-[10px] font-bold text-slate-500">REALTIME</span>
                  </div>
               </div>
               <canvas id="trendChart" class="w-full h-[300px]"></canvas>
            </div>
            
            <div class="glass-card p-8 rounded-3xl flex flex-col">
               <h4 class="font-bold mb-6 flex items-center gap-3">
                 <i class="bi bi-speedometer text-brand-500"></i>
                 مؤشرات السيادة (KPIs)
               </h4>
               <div id="kpiList" class="flex-1 space-y-6 overflow-y-auto scroll-dark pr-2">
                 <!-- KPIs will be injected here -->
               </div>
               <div class="mt-6 pt-4 border-t border-white/5">
                 <select id="kpiWindow" class="w-full bg-brand-950 border border-white/5 rounded-xl px-4 py-2 text-sm text-slate-400 outline-none focus:border-brand-500">
                    <option value="300">آخر 5 دقائق</option>
                    <option value="1800" selected>آخر 30 دقيقة</option>
                    <option value="3600">ساعة كاملة</option>
                 </select>
               </div>
            </div>
          </div>
        </section>

        <!-- Tab: Chat -->
        <section id="view-chat" class="hidden h-full flex flex-col animate-entry">
          <div class="flex-1 glass-card rounded-3xl flex flex-col overflow-hidden max-w-4xl mx-auto w-full shadow-2xl">
            <!-- Chat Logs -->
            <div id="chatMessages" class="flex-1 overflow-y-auto p-8 space-y-8 scroll-dark bg-brand-950/20">
              <div class="flex gap-4 items-start max-w-[85%]">
                <div class="w-10 h-10 rounded-xl bg-brand-600/20 border border-brand-500/30 flex items-center justify-center shrink-0">
                  <i class="bi bi-robot text-brand-400"></i>
                </div>
                <div class="bg-white/[0.03] border border-white/5 p-4 rounded-2xl rounded-tr-none text-slate-200 leading-relaxed text-sm">
                  أهلاً بك في فضاء <strong>نوقة</strong> السيادي. أنا جاهزة لتحليل أفكارك وتنفيذ أوامرك.
                </div>
              </div>
            </div>

            <!-- Input Area -->
            <div class="p-6 bg-[#0D1117] border-t border-white/5">
              <div class="relative group">
                <textarea id="chatInput" rows="2" 
                  class="w-full bg-brand-950 border border-white/5 rounded-2xl px-6 py-4 pr-16 text-slate-200 outline-none focus:border-brand-500/50 focus:ring-4 focus:ring-brand-500/5 transition-all resize-none placeholder-slate-600 text-sm"
                  placeholder="اسأل نوقة..."></textarea>
                <button id="sendButton" title="إرسال" onclick="sendChatMessage()" 
                  class="absolute left-4 bottom-4 w-10 h-10 rounded-xl bg-brand-600 hover:bg-brand-500 text-white flex items-center justify-center transition-all shadow-lg shadow-brand-500/20 hover:scale-105 active:scale-95">
                  <i class="bi bi-send-fill fs-5"></i>
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Tab: Alerts -->
        <section id="view-alerts" class="hidden animate-entry">
          <div class="glass-card rounded-3xl overflow-hidden">
             <div class="p-8 border-b border-white/5 flex justify-between items-center bg-brand-950/10">
                <h4 class="font-bold flex items-center gap-3">
                  <i class="bi bi-bell text-orange-500"></i>
                  سجل التنبيهات السيادية
                </h4>
                <div class="flex gap-3">
                  <select id="alertsLimit" class="bg-brand-950 border border-white/5 rounded-lg px-3 py-1 text-xs outline-none">
                    <option value="50">أحدث 50</option>
                    <option value="200" selected>أحدث 200</option>
                  </select>
                  <button onclick="clearAlerts()" class="px-4 py-1 rounded-lg bg-red-500/10 text-red-500 text-xs font-bold hover:bg-red-500/20 transition-all border border-red-500/20">
                    مسح الكل
                  </button>
                </div>
             </div>
             <div id="alertsContainer" class="p-8 space-y-4">
                <div class="text-center py-20 text-slate-600">
                  <i class="bi bi-shield-check text-4xl mb-4 block opacity-20"></i>
                  <p>لا توجد تنبيهات نشطة حالياً. النظام مستقر.</p>
                </div>
             </div>
          </div>
        </section>

        <!-- Tab: Control -->
        <section id="view-control" class="hidden animate-entry">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="glass-card p-8 rounded-3xl">
              <h4 class="font-bold mb-6 flex items-center gap-3">
                <i class="bi bi-activity text-brand-500"></i>
                إدارة الدورة الذاتية
              </h4>
              <p class="text-sm text-slate-500 mb-8 leading-relaxed">تحكم في وتيرة عمل النظام الذاتي وتدخلاته السيادية في البيئة المضيفة.</p>
              
              <div class="space-y-6">
                <div>
                  <label class="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-3">الفاصل الزمني (ثواني)</label>
                  <input type="number" id="autonomicIntervalInput" value="60" 
                    class="w-full bg-brand-950 border border-white/5 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-brand-500/50">
                </div>
                <div class="grid grid-cols-2 gap-4 pt-4">
                  <button onclick="startAutonomic()" class="bg-brand-600 hover:bg-brand-500 text-white py-3 rounded-xl font-bold transition-all shadow-lg shadow-brand-500/10">
                    تشغيل
                  </button>
                  <button onclick="stopAutonomic()" class="bg-white/5 hover:bg-white/10 text-slate-300 py-3 rounded-xl font-bold transition-all border border-white/5">
                    إيقاف
                  </button>
                </div>
                <div id="autonomicInfo" class="mt-6 p-4 rounded-xl bg-brand-950/40 border border-white/5 text-xs mono text-slate-500">
                   Status: Waiting for input...
                </div>
              </div>
            </div>

            <div class="glass-card p-8 rounded-3xl">
              <h4 class="font-bold mb-6 flex items-center gap-3">
                <i class="bi bi-download text-brand-500"></i>
                تصدير البيانات والتقارير
              </h4>
              <p class="text-sm text-slate-500 mb-8 leading-relaxed">استخراج البيانات التاريخية للنظام بصيغ معيارية للتحليل الخارجي.</p>
              
              <div class="space-y-6">
                 <div>
                   <label class="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-3">نافذة التصدير</label>
                   <select id="exportWindow" class="w-full bg-brand-950 border border-white/5 rounded-xl px-4 py-3 text-slate-200 outline-none focus:border-brand-500/50">
                     <option value="3600">آخر ساعة</option>
                     <option value="86400" selected>آخر 24 ساعة</option>
                     <option value="604800">آخر أسبوع</option>
                   </select>
                 </div>
                 <div class="flex gap-8 py-2">
                    <label class="flex items-center gap-2 cursor-pointer group">
                      <input type="radio" name="exportFormat" value="json" checked class="accent-brand-500">
                      <span class="text-sm text-slate-400 group-hover:text-white transition-colors">JSON Format</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer group">
                      <input type="radio" name="exportFormat" value="csv" class="accent-brand-500">
                      <span class="text-sm text-slate-400 group-hover:text-white transition-colors">CSV Table</span>
                    </label>
                 </div>
                 <button onclick="exportAnalytics()" class="w-full bg-white/5 hover:bg-white/10 text-white py-3 rounded-xl font-bold transition-all border border-white/5 flex items-center justify-center gap-2 mt-4">
                    <i class="bi bi-file-earmark-arrow-down"></i>
                    توليد وتحميل الملف
                 </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>

  <script nonce="{nonce}" src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<script nonce="{nonce}">
    // Core State
    let activeTab = 'analytics';
    let trendChart = null;
    let apiKey = localStorage.getItem('noogh_api_key') || '';
    let jwtToken = localStorage.getItem('noogh_token') || '';
    // Tab Management
    function switchTab(tabId) {{
      document.querySelectorAll('.nav-item').forEach(btn => {{
        btn.classList.toggle('bg-white/10', btn.id === `btn-${{tabId}}`);
        btn.classList.toggle('text-brand-400', btn.id === `btn-${{tabId}}`);
      }});

      document.querySelectorAll('section[id^="view-"]').forEach(view => {{
        view.classList.toggle('hidden', view.id !== `view-${{tabId}}`);
      }});
      
      activeTab = tabId;
      if (tabId === 'analytics') loadTrends();
    }}

    // Auth & API
    async function apiCall(endpoint, options = {{}}) {{
      const headers = {{
        'Content-Type': 'application/json',
        ...options.headers
      }};
      if (jwtToken) headers['Authorization'] = `Bearer ${{jwtToken}}`;
      if (apiKey) headers['X-API-Key'] = apiKey;

      const resp = await fetch(endpoint, {{ ...options, headers }});
      if (resp.status === 401 || resp.status === 403) {{
        promptForLogin();
        throw new Error('Unauthorized');
      }}
      if (!resp.ok) return {{ error: await resp.text() }};
      return await resp.json();
    }}

    async function promptForLogin() {{
      const password = prompt("🔐 السيادة تتطلب مصادقة. أدخل مفتاح الوصول:");
      if (!password) return;
      
      const resp = await apiCall('/api/dashboard/auth/login', {{
        method: 'POST',
        body: JSON.stringify({{ api_key: password }})
      }});
      
      if (resp.token) {{
        jwtToken = resp.token;
        localStorage.setItem('noogh_token', jwtToken);
        location.reload();
      }} else {{
        alert("❌ مفتاح غير صالح");
      }}
    }}

    function updateCurrentTime() {{
      const now = new Date();
      document.getElementById('currentTime').textContent = now.toLocaleTimeString('ar-SA', {{ hour: '2-digit', minute: '2-digit' }});
    }}
    setInterval(updateCurrentTime, 1000);

    // Data Loading
    async function loadStats() {{
      const data = await apiCall('/api/dashboard/stats');
      if (data.error) return;

      const isOnline = data.neural?.status === 'online';
      const pulse = document.getElementById('neuralPulse');
      pulse.className = `status-pulse ${{isOnline ? 'bg-green-500' : 'bg-red-500'}}`;
      document.getElementById('neuralText').textContent = isOnline ? 'النواة نشطة' : 'النواة غير متصلة';
      document.getElementById('latencyText').textContent = `RTT: ${{data.neural?.latency_ms || '--'}}ms`;

      document.getElementById('statNeural').textContent = isOnline ? 'Active' : 'Offline';
      document.getElementById('statEvents').textContent = data.store?.total_events || 0;
      document.getElementById('statAlerts').textContent = data.alerts?.count || 0;
      document.getElementById('statNeuralMeta').textContent = data.neural?.base || '0.0.0.0';
    }}

    async function loadKPIs() {{
      const window = document.getElementById('kpiWindow').value;
      const data = await apiCall(`/api/dashboard/analytics/kpis?window=${{window}}`);
      const container = document.getElementById('kpiList');
      if (data.error) return;
      
      const kpis = data.kpis || data;
      const mapping = [
        ['success_rate', 'معدل النجاح', '%'],
        ['approval_rate', 'معدل القبول', '%'],
        ['avg_confidence', 'متوسط الثقة', ''],
        ['health_score', 'درجة الصحة', '']
      ];

      container.innerHTML = mapping.map(([key, label, unit]) => {{
        const val = kpis[key] || 0;
        const percent = key.includes('rate') ? val : (val * 10);
        return `
          <div class="space-y-2">
            <div class="flex justify-between text-xs font-medium">
              <span class="text-slate-400 font-bold">${{label}}</span>
              <span class="text-brand-400 font-mono">${{typeof val === 'number' ? val.toFixed(1) : val}}${{unit}}</span>
            </div>
            <div class="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
              <div class="h-full bg-gradient-to-r from-brand-600 to-indigo-400 transition-all duration-1000" style="width: ${{percent}}%"></div>
            </div>
          </div>
        `;
      }}).join('');
    }}

    async function loadTrends() {{
      const data = await apiCall('/api/dashboard/analytics/trends?window=3600&buckets=15');
      if (data.error) return;
      const buckets = data.buckets || [];
      const ctx = document.getElementById('trendChart').getContext('2d');
      
      if (trendChart) trendChart.destroy();
      
      trendChart = new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: buckets.map(b => new Date(b.timestamp * 1000).toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}})),
          datasets: [{{
            label: 'Events',
            data: buckets.map(b => b.events_count),
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }},
            y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }}
          }}
        }}
      }});
    }}

    async function loadAlerts() {{
      const limit = document.getElementById('alertsLimit').value;
      const data = await apiCall(`/api/dashboard/alerts/history?limit=${{limit}}`);
      if (data.error) return;
      const container = document.getElementById('alertsContainer');
      const alerts = data.alerts || [];

      if (!alerts.length) {{
        container.innerHTML = '<div class="text-center py-20 text-slate-600"><p>لا توجد تنبيهات.</p></div>';
        return;
      }}

      container.innerHTML = alerts.slice().reverse().map(a => `
        <div class="glass-card p-4 rounded-xl border-r-4 border-orange-500/50 flex justify-between items-center group">
          <div>
            <p class="text-sm font-bold text-white mb-1">${{a.message}}</p>
            <p class="text-[10px] mono text-slate-500 uppercase">${{new Date(a.ts * 1000).toLocaleString('ar-SA')}}</p>
          </div>
          <span class="px-2 py-0.5 rounded bg-orange-500/10 text-orange-500 text-[10px] font-bold">${{a.level}}</span>
        </div>
      `).join('');
    }}

    async function clearAlerts() {{
      if (!confirm('مسح جميع التنبيهات؟')) return;
      await apiCall('/api/dashboard/alerts/clear', {{ method: 'POST' }});
      await loadAlerts();
      await loadStats();
    }}

    // Autonomic Controls
    async function startAutonomic() {{
      const interval = document.getElementById('autonomicIntervalInput').value;
      await apiCall(`/api/dashboard/autonomic/start?interval=${{interval}}`, {{ method: 'POST' }});
      refreshAutonomic();
    }}

    async function stopAutonomic() {{
      await apiCall('/api/dashboard/autonomic/stop', {{ method: 'POST' }});
      refreshAutonomic();
    }}

    async function refreshAutonomic() {{
      const data = await apiCall('/api/dashboard/autonomic/status');
      if (data.error) return;
      const running = data.running || data.is_running;
      document.getElementById('statAutonomic').textContent = running ? 'Active' : 'Stopped';
      document.getElementById('autonomicInfo').textContent = `Status: ${{running ? 'RUNNING' : 'STOPPED'}} | Interval: ${{data.interval ?? data.status?.interval}}s`;
    }}

    async function exportAnalytics() {{
      const window = document.getElementById('exportWindow').value;
      const fmt = document.querySelector('input[name="exportFormat"]:checked').value;
      const data = await apiCall(`/api/dashboard/analytics/export?window=${{window}}&fmt=${{fmt}}`);
      if (data.error) return alert(data.error);
      
      const blob = new Blob([fmt === 'json' ? JSON.stringify(data, null, 2) : data], {{ type: fmt === 'json' ? 'application/json' : 'text/csv' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `noogh_export_${{Date.now()}}.${{fmt}}`;
      a.click();
      URL.revokeObjectURL(url);
    }}

    // Chat Implementation
    function addChatMessage(role, text) {{
      const container = document.getElementById('chatMessages');
      const isAI = role === 'bot';
      
      // Thought Parsing
      let thought = '';
      let answer = text;
      const thoughtMatch = text.match(/(?:THINK:|نوقة \\(تفكير\\):)([\\s\\S]*?)(?:\\n\\n|---|$)/);
      if (thoughtMatch) {{
        thought = thoughtMatch[1].trim();
        answer = text.replace(thoughtMatch[0], '').trim();
      }}

      // Format answer: convert newlines to <br>, detect code output
      if (isAI) {{
        // Normalize: handle both literal \\n from JSON and real newlines
        var NL = String.fromCharCode(10);
        answer = answer.replace(/\\\\n/g, NL);
        var fmtLines = answer.split(NL);
        var isCodeOutput = fmtLines.length > 2 && fmtLines.some(function(l) {{ return /^(total |drwx|[-lrwx]{{7,}}|Filesystem|\/dev|CONTAINER|PID |UID )/.test(l.trim()); }});
        if (isCodeOutput) {{
          var escaped = answer.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
          answer = '<pre style="background:rgba(0,0,0,0.3);padding:12px;border-radius:8px;overflow-x:auto;font-size:12px;line-height:1.6;direction:ltr;text-align:left;white-space:pre-wrap;">' + escaped + '</pre>';
        }} else {{
          answer = answer.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
          answer = answer.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
          answer = answer.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.1);padding:2px 6px;border-radius:4px;font-size:12px;">$1</code>');
          answer = fmtLines.join('<br>');
        }}
      }}

      const html = `
        <div class="flex gap-4 items-start ${{isAI ? '' : 'flex-row-reverse animate-entry'}}">
          <div class="w-10 h-10 rounded-xl ${{isAI ? 'bg-brand-600/20 border-brand-500/30' : 'bg-white/10 border-white/20'}} border flex items-center justify-center shrink-0">
            <i class="bi ${{isAI ? 'bi-robot text-brand-400' : 'bi-person text-slate-400'}}"></i>
          </div>
          <div class="max-w-[80%] space-y-4">
            ${{thought ? `
              <div class="thought-block p-4 rounded-2xl border border-white/5 text-xs text-slate-500 italic leading-relaxed">
                <p class="font-bold mb-2 not-italic text-[10px] text-brand-500 uppercase tracking-widest">تفكير نوقة</p>
                ${{thought}}
              </div>
            ` : ''}}
            <div class="${{isAI ? 'bg-white/[0.03] border-white/5 rounded-tr-none' : 'bg-brand-600 text-white rounded-tl-none'}} border p-4 rounded-2xl leading-relaxed text-sm shadow-xl">
              ${{answer}}
            </div>
          </div>
        </div>
      `;
      
      container.insertAdjacentHTML('beforeend', html);
      container.scrollTop = container.scrollHeight;
    }}

    async function sendChatMessage() {{
      const input = document.getElementById('chatInput');
      const text = input.value.trim();
      if (!text) return;

      addChatMessage('user', text);
      input.value = '';
      
      const data = await apiCall('/api/dashboard/chat/proxy', {{
        method: 'POST',
        body: JSON.stringify({{ message: text }})
      }});

      if (data.response) addChatMessage('bot', data.response);
    }}

    // Initialization
    async function init() {{
      await loadStats();
      await loadKPIs();
      await loadTrends();
      await loadAlerts();
      await refreshAutonomic();
    }}

    init();
    setInterval(loadStats, 10000);
    setInterval(loadKPIs, 30000);
    setInterval(loadAlerts, 30000);

    // Event Listeners
    document.getElementById('chatInput').addEventListener('keydown', e => {{
      if (e.key === 'Enter' && !e.shiftKey) {{
        e.preventDefault();
        sendChatMessage();
      }}
    }});
  </script>

</body>
</html>
"""


# =============================================================================
# NOTE: ensure you include router + public_router in app startup
# =============================================================================
