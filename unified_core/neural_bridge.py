"""
Neural Engine Bridge - Connects Neural Engine to AI Core Pipeline

This bridge ensures that all Neural Engine reasoning goes through
GravityWell decision authority, maintaining:
- Decision commitment via ConsequenceEngine
- Memory blocking via CoerciveMemory
- Failure scarring via ScarTissue

All decisions are IRREVERSIBLE.
"""

import asyncio
import hashlib
import logging
import time
import os
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import aiohttp

from .evolution import evolution_config as config

logger = logging.getLogger("unified_core.neural_bridge")


class CircuitBreaker:
    """Prevents cascading failures when LLM backend is down.
    
    State machine:
      CLOSED  → requests flow normally; failures increment counter
      OPEN    → all requests rejected immediately; waits for recovery_timeout
      HALF_OPEN → allows ONE probe request; success → CLOSED, failure → OPEN
    """
    CLOSED, OPEN, HALF_OPEN = "closed", "open", "half_open"
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._success_count = 0
    
    def can_execute(self) -> bool:
        """Check if a request is allowed."""
        if self.state == self.CLOSED:
            return True
        if self.state == self.OPEN:
            # Check if recovery timeout has elapsed
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self.state = self.HALF_OPEN
                logger.info("🔌 Circuit breaker → HALF_OPEN (probing)")
                return True
            return False
        # HALF_OPEN: allow one probe
        return True
    
    def record_success(self):
            """Record a successful request."""
            if self.state != self.HALF_OPEN:
                logger.debug("State was not HALF_OPEN; transitioning to CLOSED.")
            else:
                logger.info("🔌 Circuit breaker → CLOSED (probe succeeded)")

            self.state = self.CLOSED
            self._failure_count = 0
            self._success_count += 1
    
    def record_failure(self):
            """Record a failed request."""
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self.state == self.HALF_OPEN:
                self.state = self.OPEN
                logger.warning("🔌 Circuit breaker → OPEN (probe failed)")
                return

            if self._failure_count < self.failure_threshold:
                return

            self.state = self.OPEN
            logger.warning(
                f"🔌 Circuit breaker → OPEN after {self._failure_count} failures. "
                f"Recovery in {self.recovery_timeout}s"
            )
    
    @property
    def stats(self) -> Dict[str, Any]:
            if not hasattr(self, 'state'):
                logger.warning("Attribute 'state' is missing, setting to None")
                state = None
            else:
                state = self.state

            if not hasattr(self, '_failure_count'):
                logger.warning("Attribute '_failure_count' is missing, setting to 0")
                failure_count = 0
            else:
                failure_count = self._failure_count

            if not hasattr(self, '_success_count'):
                logger.warning("Attribute '_success_count' is missing, setting to 0")
                success_count = 0
            else:
                success_count = self._success_count

            return {
                "state": state,
                "failures": failure_count,
                "successes": success_count,
            }

@dataclass
class NeuralRequest:
    """Request to Neural Engine with AI Core authority."""
    query: str
    context: Optional[Dict[str, Any]] = None
    urgency: float = 0.5
    require_decision: bool = True
    pre_fill: Optional[str] = None
    request_id: str = field(default_factory=lambda: hashlib.sha256(
        f"{time.time()}".encode()
    ).hexdigest()[:16])


@dataclass
class NeuralResponse:
    """Response from Neural Engine with decision commitment."""
    success: bool
    content: str
    decision_id: Optional[str] = None
    commitment_hash: Optional[str] = None
    blocked: bool = False
    block_reason: Optional[str] = None
    thinking_process: Optional[str] = None
    confidence: float = 0.0
    sources_used: List[str] = field(default_factory=list)
    raw_response: str = ""


class NeuralEngineClient:
    """
    HTTP Client for Neural Engine API.
    
    Supports two modes:
    - 'local': Connects to NOOGH's own Neural Engine (/api/v1/process)
    - 'vllm':  Connects to vLLM OpenAI-compatible API (/v1/chat/completions)
    
    Mode is auto-detected from NEURAL_ENGINE_MODE env var.
    """
    
    # System prompt used when calling vLLM in chat mode
    VLLM_SYSTEM_PROMPT = (
        "أنت NOOGH، وكيل ذكاء اصطناعي سيادي (Sovereign AI Agent). "
        "مهامك: تحليل الأنظمة، حماية البنية التحتية، التخطيط الذاتي، "
        "وتحسين الأداء. فكّر خطوة بخطوة واشرح أسبابك."
    )
    
    def __init__(self, base_url: str = None, mode: str = None):
        if base_url is None:
            # v21: RUNPOD_BRAIN_URL (primary brain) > NEURAL_ENGINE_URL (legacy/local)
            base_url = os.getenv("RUNPOD_BRAIN_URL") or os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")
        self._base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Mode: 'local' (Neural Engine) or 'vllm' (OpenAI-compatible)
        self._mode = mode or os.getenv("NEURAL_ENGINE_MODE", "local")
        
        # Timeout: longer for remote vLLM calls
        timeout_seconds = int(os.getenv("NEURAL_TIMEOUT_SECONDS", "600" if self._mode == "vllm" else "120"))
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        
        # vLLM model name
        self._vllm_model = os.getenv("VLLM_MODEL_NAME", "noogh-teacher")
        self._vllm_max_tokens = int(os.getenv("VLLM_MAX_TOKENS", "4096"))
        self._vllm_context_length = int(os.getenv("VLLM_CONTEXT_LENGTH", "4096"))
        
        # v21: API key for cloud providers (DeepSeek, OpenAI, etc.)
        self._api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        # v21: Detect external URLs (RunPod, DeepSeek) — use requests instead of aiohttp
        self._is_external = self._base_url.startswith("https://")
        self._vllm_temperature = config.VLLM_TEMPERATURE
        
        # Retry settings (from centralized config)
        self._max_retries = config.NEURAL_MAX_RETRIES if self._mode == "vllm" else 1
        
        # v1.1: Circuit breaker
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=config.CB_FAILURE_THRESHOLD,
            recovery_timeout=config.CB_RECOVERY_TIMEOUT
        )
        
        logger.info(
            f"🧠 NeuralEngineClient initialized: mode={self._mode} "
            f"url={self._base_url} model={self._vllm_model if self._mode == 'vllm' else 'local'}"
        )
        
        # v1.2: TTL-based result cache
        self._cache: OrderedDict[str, Tuple[float, Any]] = OrderedDict()
        self._cache_ttl = config.NEURAL_CACHE_TTL  # seconds
        self._cache_max_size = 64
    
    # ── v1.2: Async Context Manager ──────────────────────────────
    
    async def __aenter__(self):
        """Enter session context — creates aiohttp session."""
        await self._get_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit session context — closes aiohttp session."""
        await self.close()
        return False
    
    @property
    def mode(self) -> str:
        return self._mode
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with UDS support for max performance."""
        if self._session is None or self._session.closed:
            uds = os.getenv("NEURAL_UDS")
            if uds and self._mode == "local":
                # Use Unix Domain Socket for zero-overhead local communication
                connector = aiohttp.UnixConnector(path=uds)
                self._base_url = "http://localhost"
                self._session = aiohttp.ClientSession(connector=connector, timeout=self._timeout)
                logger.info(f"🔗 Neural Bridge: Unix Socket Connection Active ({uds})")
            else:
                self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session
    
    async def close(self):
        """Close HTTP session and clear cache."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._cache.clear()
    
    # ── v1.2: TTL Cache ──────────────────────────────────────────
    
    def _cache_key(self, query: str, context: Optional[Dict]) -> str:
        """Generate a cache key from query + context."""
        raw = query + (str(sorted(context.items())) if context else "")
        return hashlib.sha256(raw.encode()).hexdigest()[:24]
    
    def _cache_get(self, key: str) -> Optional[Any]:
            """Get a cached result if still within TTL."""
            if key not in self._cache:
                return None

            ts, value = self._cache[key]
            if time.time() - ts >= self._cache_ttl:
                del self._cache[key]
                return None

            self._cache.move_to_end(key)  # LRU refresh
            return value
    
    def _cache_set(self, key: str, value: Any):
        """Store a result in cache with current timestamp."""
        self._cache[key] = (time.time(), value)
        # Evict oldest if over max size
        while len(self._cache) > self._cache_max_size:
            self._cache.popitem(last=False)
    
    async def health_check(self) -> bool:
        """Check Neural Engine health (mode-aware). Uses requests for external HTTPS."""
        try:
            if self._is_external:
                # v21: Use requests for external HTTPS (aiohttp hangs on RunPod proxy)
                import requests as _requests
                try:
                    url = f"{self._base_url}/v1/models" if self._mode == "vllm" else f"{self._base_url}/health"
                    r = _requests.get(url, timeout=5)
                    if r.status_code == 200 and self._mode == "vllm":
                        models = [m.get('id', '') for m in r.json().get('data', [])]
                        logger.debug(f"vLLM healthy (external), models: {models}")
                    return r.status_code == 200
                except Exception as e:
                    logger.warning(f"Neural Engine health check failed (external): {e}")
                    return False
            else:
                session = await self._get_session()
                if self._mode == "vllm":
                    async with session.get(f"{self._base_url}/v1/models") as resp:
                        healthy = resp.status == 200
                        if healthy:
                            data = await resp.json()
                            models = [m.get("id", "") for m in data.get("data", [])]
                            logger.debug(f"vLLM healthy, models: {models}")
                        return healthy
                else:
                    async with session.get(f"{self._base_url}/health") as resp:
                        return resp.status == 200
        except Exception as e:
            logger.warning(f"Neural Engine health check failed ({self._mode}): {e}")
            return False
    
    async def _call_with_retry(self, coro_func, *args, **kwargs) -> Any:
        """Call an async function with retry logic and circuit breaker."""
        if not self._circuit_breaker.can_execute():
            raise ConnectionError(
                f"Circuit breaker OPEN — LLM unavailable. "
                f"Recovery in {self._circuit_breaker.recovery_timeout}s"
            )
        
        last_error = None
        for attempt in range(self._max_retries):
            try:
                result = await coro_func(*args, **kwargs)
                self._circuit_breaker.record_success()
                return result
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                last_error = e
                self._circuit_breaker.record_failure()
                if attempt < self._max_retries - 1:
                    wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Neural call attempt {attempt+1}/{self._max_retries} failed: {e}. "
                        f"Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
        raise last_error
    
    async def think(
        self, 
        query: str, 
        context: Optional[Dict] = None,
        depth: str = "standard",
        pre_fill: str = None
    ) -> Dict[str, Any]:
        """
        Send thinking request — routes to vLLM or local Neural Engine.
        """
        if self._mode == "vllm":
            return await self._think_vllm(query, context, depth, pre_fill)
        else:
            return await self._think_local(query, context, depth, pre_fill)
    
    async def _think_vllm(
        self,
        query: str,
        context: Optional[Dict] = None,
        depth: str = "standard",
        pre_fill: str = None
    ) -> Dict[str, Any]:
        """
        Think via vLLM OpenAI-compatible API (/v1/chat/completions).
        Uses requests library for external HTTPS URLs (RunPod proxy hangs with aiohttp).
        """
        # Build chat messages
        system_content = self.VLLM_SYSTEM_PROMPT
        if context:
            ctx_str = ", ".join(f"{k}: {v}" for k, v in context.items() if v)
            if ctx_str:
                system_content += f"\n\nسياق إضافي: {ctx_str}"
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query}
        ]
        
        if pre_fill:
            messages.append({"role": "assistant", "content": pre_fill})
        
        # Dynamic max_tokens
        input_text = " ".join(m.get("content", "") for m in messages)
        estimated_input_tokens = len(input_text) // 3 + 50
        available_tokens = max(self._vllm_context_length - estimated_input_tokens, 256)
        effective_max_tokens = min(self._vllm_max_tokens, available_tokens)
        
        payload = {
            "model": self._vllm_model,
            "messages": messages,
            "temperature": self._vllm_temperature,
            "max_tokens": effective_max_tokens,
        }
        
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        
        try:
            if self._is_external:
                # v21: Use requests in thread for external HTTPS (aiohttp hangs on RunPod proxy)
                result = await self._call_external(payload, headers)
            else:
                result = await self._call_local_aiohttp(payload, headers)
            
            self._circuit_breaker.record_success()
            return result
        except asyncio.TimeoutError:
            self._circuit_breaker.record_failure()
            logger.error(f"vLLM request timed out (>{self._timeout.total}s)")
            return {"error": "Timeout", "success": False, "timeout": True}
        except Exception as e:
            self._circuit_breaker.record_failure()
            logger.error(f"vLLM think error [{type(e).__name__}]: {e}")
            return {"error": str(e), "success": False}
    
    async def _call_external(self, payload: dict, headers: dict) -> Dict[str, Any]:
        """Call external HTTPS API using requests in thread executor (aiohttp hangs on RunPod)."""
        import requests as _requests
        
        def _sync_call():
            start_time = time.time()
            resp = _requests.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=int(self._timeout.total or 120),
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                logger.info(
                    f"🧠 vLLM response: {usage.get('completion_tokens', '?')} tokens, "
                    f"{latency_ms}ms (external)"
                )
                return {
                    "thought_process": "",
                    "content": content,
                    "confidence": 0.90,
                    "insights": [],
                    "raw_response": content,
                    "usage": usage,
                    "latency_ms": latency_ms,
                    "success": True,
                }
            else:
                error = resp.text
                logger.error(f"vLLM external failed [{resp.status_code}]: {error[:200]}")
                return {"error": error, "success": False}
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_call)
    
    async def _call_local_aiohttp(self, payload: dict, headers: dict) -> Dict[str, Any]:
        """Call local Ollama/vLLM using aiohttp (fast for localhost)."""
        session = await self._get_session()
        start_time = time.time()
        async with session.post(
            f"{self._base_url}/v1/chat/completions",
            json=payload,
            headers=headers
        ) as resp:
            latency_ms = int((time.time() - start_time) * 1000)
            if resp.status == 200:
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                logger.info(
                    f"🧠 vLLM response: {usage.get('completion_tokens', '?')} tokens, "
                    f"{latency_ms}ms"
                )
                return {
                    "thought_process": "",
                    "content": content,
                    "confidence": 0.85,
                    "insights": [],
                    "raw_response": content,
                    "usage": usage,
                    "latency_ms": latency_ms,
                }
            else:
                error = await resp.text()
                logger.error(f"vLLM think failed [{resp.status}]: {error}")
                return {"error": error, "success": False}
    
    async def _think_local(
        self,
        query: str,
        context: Optional[Dict] = None,
        depth: str = "standard",
        pre_fill: str = None
    ) -> Dict[str, Any]:
        """
        Think via local Neural Engine (/api/v1/process) — original path.
        """
        try:
            session = await self._get_session()
            
            payload = {
                "text": query,
                "context": context or {},
                "store_memory": True
            }
            
            if pre_fill:
                payload["pre_fill"] = pre_fill
            
            token = os.getenv("NOOGH_INTERNAL_TOKEN", "dev-token-noogh-2026")
            headers = {
                "X-Internal-Token": token,
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{self._base_url}/api/v1/process",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "thought_process": "\n".join(data.get("reasoning_trace", [])),
                        "content": data.get("conclusion", ""),
                        "confidence": data.get("confidence", 0.8),
                        "insights": data.get("suggested_actions", []),
                        "raw_response": data.get("raw_response", "")
                    }
                else:
                    error = await resp.text()
                    logger.error(f"Neural Engine think failed: {error}")
                    return {"error": error, "success": False}
                    
        except asyncio.TimeoutError:
            logger.error("Neural Engine request timed out")
            return {"error": "Timeout", "success": False, "timeout": True}
        except aiohttp.ClientError as e:
            logger.error(f"Neural Engine connection error: {e}")
            return {"error": str(e), "success": False, "connection_failed": True}
        except Exception as e:
            logger.error(f"Neural Engine unexpected error: {e}")
            return {"error": str(e), "success": False}

    async def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Direct LLM completion — bypasses chatbot system prompt and ReAct loop.
        Used for code generation tasks where the caller provides custom system prompt.
        Routes to vLLM or local Neural Engine based on mode.
        
        Args:
            timeout: Request timeout in seconds (default 120)
        """
        if self._mode == "vllm":
            result = await self._complete_vllm(messages, max_tokens, timeout)
            # v1.4: Fallback to local if vLLM fails (network, server down)
            if not result.get("success"):
                logger.warning(
                    f"⚠️ vLLM failed ({result.get('error', 'unknown')}), "
                    f"falling back to local Neural Engine"
                )
                result = await self._complete_local(messages, max_tokens, timeout)
            return result
        else:
            return await self._complete_local(messages, max_tokens, timeout)
    
    async def _complete_vllm(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Complete via vLLM — uses SSE streaming to bypass Cloudflare 100s timeout.
        Streaming keeps the connection alive so Cloudflare doesn't terminate it.
        """
        async def _do_call():
            session = await self._get_session()
            
            # v9: Dynamic max_tokens — cap to fit context window
            input_text = " ".join(m.get("content", "") for m in messages)
            estimated_input_tokens = len(input_text) // 3 + 50
            available_tokens = max(self._vllm_context_length - estimated_input_tokens, 256)
            effective_max_tokens = min(max_tokens, available_tokens)
            
            payload = {
                "model": self._vllm_model,
                "messages": messages,
                "max_tokens": effective_max_tokens,
                "temperature": self._vllm_temperature,
                "stream": True,  # v12: SSE streaming to bypass Cloudflare 100s timeout
            }
            
            req_timeout = aiohttp.ClientTimeout(total=timeout)
            collected_content = []
            finish_reason = "unknown"
            usage = {}
            
            # v21: Build headers with optional API key auth
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            
            if self._is_external:
                # v21: Use requests in thread for external HTTPS (aiohttp hangs)
                import requests as _requests
                
                def _sync_complete():
                    start_time = time.time()
                    # Use non-streaming for external (simpler, more reliable)
                    payload_copy = dict(payload)
                    payload_copy["stream"] = False
                    resp = _requests.post(
                        f"{self._base_url}/v1/chat/completions",
                        json=payload_copy,
                        headers=headers,
                        timeout=timeout,
                    )
                    latency_ms = int((time.time() - start_time) * 1000)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        finish_reason = data["choices"][0].get("finish_reason", "stop")
                        logger.info(f"🧠 vLLM complete: {usage.get('completion_tokens', '?')} tokens, {latency_ms}ms (external)")
                        return {
                            "content": content,
                            "finish_reason": finish_reason,
                            "usage": usage,
                            "latency_ms": latency_ms,
                            "success": True,
                        }
                    else:
                        return {"error": resp.text[:200], "status": resp.status_code}
                
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, _sync_complete)
            
            req_timeout = aiohttp.ClientTimeout(total=timeout)
            collected_content = []
            finish_reason = "unknown"
            usage = {}
            
            async with session.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=req_timeout
            ) as resp:
                if resp.status == 200:
                    # Process SSE stream
                    async for line in resp.content:
                        line = line.decode("utf-8").strip()
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str == "[DONE]":
                            break
                        try:
                            import json as _json
                            chunk = _json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                collected_content.append(delta["content"])
                            chunk_finish = chunk["choices"][0].get("finish_reason")
                            if chunk_finish:
                                finish_reason = chunk_finish
                            if "usage" in chunk:
                                usage = chunk["usage"]
                        except (KeyError, ValueError):
                            continue
                    
                    content = "".join(collected_content)
                    if finish_reason == "length":
                        logger.warning(
                            f"⚠️ vLLM response truncated (finish_reason=length, "
                            f"tokens={len(collected_content)} chunks)"
                        )
                    return {
                        "content": content,
                        "success": True,
                        "usage": usage,
                        "finish_reason": finish_reason
                    }
                else:
                    error_body = await resp.text()
                    error_msg = error_body.strip() if error_body.strip() else f"HTTP {resp.status} (empty body — proxy reset?)"
                    logger.error(f"vLLM complete failed [{resp.status}]: {error_msg}")
                    return {"error": error_msg, "success": False}

        try:
            return await self._call_with_retry(_do_call)
        except aiohttp.ServerDisconnectedError as e:
            logger.error(f"vLLM complete: server disconnected (proxy timeout?): {e}")
            return {"error": f"ServerDisconnected: {e}", "success": False}
        except aiohttp.ClientConnectorError as e:
            logger.error(f"vLLM complete: connection refused: {e}")
            return {"error": f"ConnectionRefused: {e}", "success": False}
        except Exception as e:
            logger.error(f"vLLM complete error [{type(e).__name__}]: {e}")
            return {"error": str(e), "success": False}
    
    async def _complete_local(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Complete via local Neural Engine (/api/v1/complete).
        """
        try:
            req_timeout = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=req_timeout) as session:
                token = os.getenv("NOOGH_INTERNAL_TOKEN", "dev-token-noogh-2026")
                headers = {
                    "X-Internal-Token": token,
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "messages": messages,
                    "max_tokens": max_tokens
                }
                
                async with session.post(
                    f"{self._base_url}/api/v1/complete",
                    json=payload,
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "content": data.get("completion", ""),
                            "success": data.get("success", False)
                        }
                    else:
                        error = await resp.text()
                        logger.error(f"Neural Engine complete failed: {error}")
                        return {"error": error, "success": False}
                        
        except asyncio.TimeoutError:
            logger.error("Neural Engine complete request timed out")
            return {"error": "Timeout", "success": False}
        except Exception as e:
            logger.error(f"Neural Engine complete error: {e}")
            return {"error": str(e), "success": False}
    
    async def reason(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send reasoning request to Neural Engine (mapped to /process).
        """
        try:
            session = await self._get_session()
            
            payload = {
                "text": query,
                "context": {**(context or {}), "system_prompt": system_prompt, "mode": "reason"},
                "store_memory": True
            }
            
            # Load token (graceful fallback for dev environment)
            token = os.getenv("NOOGH_INTERNAL_TOKEN", "107194")
            headers = {
                "X-Internal-Token": token,
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{self._base_url}/api/v1/process",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "thought_process": "\n".join(data.get("reasoning_trace", [])),
                        "content": data.get("conclusion", ""),
                        "confidence": data.get("confidence", 0.0)
                    }
                else:
                    error = await resp.text()
                    return {"error": error, "success": False}
                    
        except aiohttp.ClientError as e:
            logger.error(f"Neural Engine reason error: {e}")
            return {"error": str(e), "success": False}


class NeuralEngineBridge:
    """
    Bridge between Neural Engine and AI Core (GravityWell).
    
    Ensures all Neural Engine responses go through:
    1. GravityWell decision authority
    2. ConsequenceEngine commitment
    3. CoerciveMemory blocking
    4. ScarTissue failure recording
    
    This maintains the IRREVERSIBILITY principle of the AI Core.
    """
    
    def __init__(
        self,
        gravity_well=None,
        consequence_engine=None,
        coercive_memory=None,
        scar_tissue=None,
        neural_client: Optional[NeuralEngineClient] = None,
        neural_url: str = None
    ):
        self._gravity_well = gravity_well
        self._consequence_engine = consequence_engine
        self._coercive_memory = coercive_memory
        self._scar_tissue = scar_tissue
        self._neural_client = neural_client or NeuralEngineClient(neural_url)
        
        # Statistics
        self._request_count = 0
        self._blocked_count = 0
        self._success_count = 0
        self._failure_count = 0
        
        logger.info("NeuralEngineBridge initialized")
    
    def set_gravity_well(self, gravity_well):
        """Set GravityWell reference."""
        self._gravity_well = gravity_well
        logger.info("NeuralEngineBridge: GravityWell connected")
    
    def set_consequence_engine(self, engine):
        """Set ConsequenceEngine reference."""
        self._consequence_engine = engine
    
    def set_coercive_memory(self, memory):
        """Set CoerciveMemory reference."""
        self._coercive_memory = memory
    
    def set_scar_tissue(self, scars):
        """Set ScarTissue reference."""
        self._scar_tissue = scars
    
    def _inflict_scar(self, request: NeuralRequest, error_msg: str, severity: str = "unknown"):
        """Inflict a scar on failure with severity classification.
        
        Args:
            request: The failed request
            error_msg: Error message for the scar
            severity: One of 'connection', 'runtime', 'unexpected'
        """
        if not self._scar_tissue:
            return
        try:
            from unified_core.core.scar import Failure
            failure = Failure(
                failure_id=hashlib.sha256(
                    f"neural_{severity}:{request.request_id}:{time.time()}".encode()
                ).hexdigest()[:16],
                action_type=f"neural_think_{severity}",
                action_params={"query": request.query[:200]},
                error_message=error_msg[:500]
            )
            self._scar_tissue.inflict(failure)
            logger.warning(f"Neural {severity} failure scarred (id={failure.failure_id})")
        except Exception as scar_err:
            logger.debug(f"Scar infliction failed: {scar_err}")
    
    async def think_with_authority(
        self, 
        request: NeuralRequest
    ) -> NeuralResponse:
        """
        Process request through Neural Engine with GravityWell authority.
        
        Flow:
        1. Check CoerciveMemory for blocks
        2. Consult GravityWell for decision
        3. If allowed, call Neural Engine
        4. Commit decision to ConsequenceEngine
        5. On failure, inflict scar via ScarTissue
        
        THIS DECISION IS IRREVERSIBLE.
        """
        self._request_count += 1
        
        # Step 1: Check CoerciveMemory for blocks
        if self._coercive_memory:
            from unified_core.core.coercive_memory import MemoryVerdict
            verdict, reason, cost = self._coercive_memory.check(
                action_type="neural_think",
                params={"query": request.query}
            )
            
            if verdict == MemoryVerdict.DISCOURAGED:
                self._blocked_count += 1
                logger.warning(f"Neural request blocked by CoerciveMemory: {reason}")
                return NeuralResponse(
                    success=False,
                    content="",
                    blocked=True,
                    block_reason=reason
                )
        
        # Step 2: Consult GravityWell for decision
        decision = None
        if self._gravity_well and request.require_decision:
            from unified_core.core.gravity import DecisionContext, DecisionType
            
            context = DecisionContext(
                query=request.query,
                urgency=request.urgency,
                constraints=request.context or {}
            )
            
            decision = self._gravity_well.decide(context)
            
            # Check if decision is to abstain
            if decision.decision_type == DecisionType.ABSTAIN:
                self._blocked_count += 1
                logger.info(f"GravityWell decided to ABSTAIN: {decision.constrained_by}")
                return NeuralResponse(
                    success=False,
                    content="",
                    blocked=True,
                    block_reason=f"Decision authority abstained: {decision.constrained_by}",
                    decision_id=decision.decision_id
                )
        
        # Step 3: Call Neural Engine
        try:
            # Check Neural Engine health first
            if not await self._neural_client.health_check():
                raise ConnectionError("Neural Engine is not available")
            
            # Call think endpoint
            result = await self._neural_client.think(
                query=request.query,
                context=request.context,
                depth="standard",
                pre_fill=request.pre_fill
            )
            
            if result.get("error"):
                raise RuntimeError(result["error"])
            
            # Step 4: Commit decision to ConsequenceEngine
            if self._consequence_engine and decision:
                from unified_core.core.consequence import Action, Outcome
                
                action = Action(
                    action_type="neural_think",
                    parameters={
                        "query": request.query,
                        "decision_id": decision.decision_id
                    }
                )
                
                outcome = Outcome(
                    success=True,
                    result={"response_length": len(str(result))}
                )
                
                self._consequence_engine.commit(action, outcome)
            
            self._success_count += 1
            
            return NeuralResponse(
                success=True,
                content=result.get("content", ""),
                decision_id=decision.decision_id if decision else None,
                commitment_hash=decision.commitment_hash if decision else None,
                thinking_process=result.get("thought_process"),
                confidence=result.get("confidence", 0.0),
                sources_used=result.get("insights", []),
                raw_response=result.get("raw_response", "")
            )
            
        except ConnectionError as e:
            # Neural Engine is down or unreachable
            self._failure_count += 1
            logger.error(f"Neural Engine unreachable: {e}")
            self._inflict_scar(request, str(e), severity="connection")
            return NeuralResponse(
                success=False,
                content=f"Neural Engine offline: {e}",
                decision_id=decision.decision_id if decision else None
            )
        
        except (asyncio.TimeoutError, TimeoutError) as e:
            # Neural Engine too slow — don't scar (transient)
            self._failure_count += 1
            logger.warning(f"Neural Engine timeout: {e}")
            return NeuralResponse(
                success=False,
                content=f"Neural Engine timeout: {e}",
                decision_id=decision.decision_id if decision else None
            )
        
        except RuntimeError as e:
            # Bad response from Neural Engine (e.g. error field in result)
            self._failure_count += 1
            logger.error(f"Neural Engine returned error: {e}")
            self._inflict_scar(request, str(e), severity="runtime")
            return NeuralResponse(
                success=False,
                content=f"Neural Engine error: {e}",
                decision_id=decision.decision_id if decision else None
            )
        
        except Exception as e:
            # Unexpected failure — scar with high severity
            self._failure_count += 1
            logger.error(f"Neural Engine unexpected failure: {type(e).__name__}: {e}")
            self._inflict_scar(request, str(e), severity="unexpected")
            return NeuralResponse(
                success=False,
                content=f"Neural Engine error: {type(e).__name__}: {e}",
                decision_id=decision.decision_id if decision else None
            )
    
    async def reason_with_authority(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict] = None,
        urgency: float = 0.5
    ) -> NeuralResponse:
        """
        Convenience method for reasoning with authority.
        """
        request = NeuralRequest(
            query=query,
            context={"system_prompt": system_prompt, **(context or {})},
            urgency=urgency
        )
        return await self.think_with_authority(request)
    
    def get_stats(self) -> Dict[str, Any]:
            """Get bridge statistics."""
            request_count = max(1, self._request_count)
            return {
                "total_requests": self._request_count,
                "blocked": self._blocked_count,
                "successful": self._success_count,
                "failed": self._failure_count,
                "block_rate": self._blocked_count / request_count,
                "success_rate": self._success_count / request_count
            }
    
    async def close(self):
        """Close the bridge and cleanup resources."""
        await self._neural_client.close()
        logger.info("NeuralEngineBridge closed")


# Module-level singleton
_bridge_instance: Optional[NeuralEngineBridge] = None


def get_neural_bridge() -> NeuralEngineBridge:
    """Get or create global NeuralEngineBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = NeuralEngineBridge()
    return _bridge_instance


async def init_neural_bridge(
    gravity_well=None,
    consequence_engine=None,
    coercive_memory=None,
    scar_tissue=None,
    neural_url: str = None,
    mode: str = None
) -> NeuralEngineBridge:
    """Initialize and configure the NeuralEngineBridge."""
    bridge = get_neural_bridge()
    
    if gravity_well:
        bridge.set_gravity_well(gravity_well)
    if consequence_engine:
        bridge.set_consequence_engine(consequence_engine)
    if coercive_memory:
        bridge.set_coercive_memory(coercive_memory)
    if scar_tissue:
        bridge.set_scar_tissue(scar_tissue)
    
    # Update neural client with URL and mode
    bridge._neural_client = NeuralEngineClient(neural_url, mode=mode)
    
    return bridge
