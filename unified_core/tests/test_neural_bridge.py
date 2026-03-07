"""
Tests for neural_bridge.py — NeuralEngineClient and NeuralEngineBridge.

Covers:
  - CircuitBreaker state machine
  - NeuralEngineClient init, mode selection, retry logic, vLLM fallback
  - NeuralEngineBridge: think_with_authority, CoerciveMemory blocking, stats
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# === Stubs to avoid heavy imports ===
import sys

# aiohttp needs real exception classes for except clauses to work
class _AiohttpStub:
    """Minimal aiohttp stub with real exception hierarchy."""
    class ClientError(Exception):
        pass
    class ClientTimeout:
        def __init__(self, total=None):
            self.total = total
    class ClientSession:
        pass
    class UnixConnector:
        def __init__(self, path=None):
            pass

if "aiohttp" not in sys.modules:
    sys.modules["aiohttp"] = _AiohttpStub()

# Stub out other heavy modules
for mod_name in [
    "unified_core.core.gravity",
    "unified_core.core.consequence",
    "unified_core.core.coercive_memory",
    "unified_core.core.scar",
]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

from unified_core.neural_bridge import (
    CircuitBreaker,
    NeuralEngineClient,
    NeuralEngineBridge,
    NeuralRequest,
    NeuralResponse,
)


# ──────────────────────────────────────────────
# CircuitBreaker
# ──────────────────────────────────────────────

class TestCircuitBreaker:
    """Tests for the CircuitBreaker state machine."""

    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitBreaker.CLOSED
        assert cb.can_execute() is True

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN
        assert cb.can_execute() is False

    def test_success_resets_counter(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb._failure_count == 0
        assert cb.state == CircuitBreaker.CLOSED

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN
        # With recovery_timeout=0, next check should transition
        assert cb.can_execute() is True
        assert cb.state == CircuitBreaker.HALF_OPEN

    def test_half_open_success_closes(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        cb.can_execute()  # → HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED

    def test_half_open_failure_reopens(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        cb.can_execute()  # → HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

    def test_stats_property(self):
        cb = CircuitBreaker()
        cb.record_success()
        cb.record_success()
        cb.record_failure()
        stats = cb.stats
        assert stats["state"] == CircuitBreaker.CLOSED
        assert stats["successes"] == 2
        assert stats["failures"] == 1

    def test_open_blocks_until_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=9999)
        cb.record_failure()
        assert cb.can_execute() is False  # timeout hasn't elapsed


# ──────────────────────────────────────────────
# NeuralEngineClient — init and config
# ──────────────────────────────────────────────

class TestNeuralEngineClientInit:
    """Tests for NeuralEngineClient initialization."""

    @patch.dict("os.environ", {}, clear=True)
    def test_default_mode_is_local(self):
        client = NeuralEngineClient()
        assert client.mode == "local"
        assert client._max_retries == 1  # local = no retries

    @patch.dict("os.environ", {"NEURAL_ENGINE_MODE": "vllm"}, clear=True)
    def test_vllm_mode_from_env(self):
        client = NeuralEngineClient()
        assert client.mode == "vllm"

    @patch.dict("os.environ", {}, clear=True)
    def test_explicit_mode_overrides_env(self):
        client = NeuralEngineClient(mode="vllm")
        assert client.mode == "vllm"

    @patch.dict("os.environ", {}, clear=True)
    def test_default_url(self):
        client = NeuralEngineClient()
        assert client._base_url == "http://127.0.0.1:8002"

    @patch.dict("os.environ", {"NEURAL_ENGINE_URL": "http://custom:9000/"}, clear=True)
    def test_url_from_env_strips_trailing_slash(self):
        client = NeuralEngineClient()
        assert client._base_url == "http://custom:9000"

    @patch.dict("os.environ", {}, clear=True)
    def test_circuit_breaker_uses_config(self):
        client = NeuralEngineClient()
        cb = client._circuit_breaker
        assert cb.failure_threshold > 0
        assert cb.recovery_timeout > 0


# ──────────────────────────────────────────────
# NeuralEngineClient — _call_with_retry
# ──────────────────────────────────────────────

class TestCallWithRetry:
    """Tests for _call_with_retry logic."""

    @pytest.fixture
    def client(self):
        with patch.dict("os.environ", {}, clear=True):
            c = NeuralEngineClient(mode="vllm")
        return c

    @pytest.mark.asyncio
    async def test_success_on_first_try(self, client):
        coro = AsyncMock(return_value={"ok": True})
        result = await client._call_with_retry(coro)
        assert result == {"ok": True}
        coro.assert_called_once()

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self, client):
        import aiohttp
        coro = AsyncMock(side_effect=[aiohttp.ClientError("fail"), {"ok": True}])
        result = await client._call_with_retry(coro)
        assert result == {"ok": True}
        assert coro.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_exhausting_retries(self, client):
        import aiohttp
        coro = AsyncMock(side_effect=aiohttp.ClientError("fail"))
        with pytest.raises(aiohttp.ClientError):
            await client._call_with_retry(coro)

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self, client):
        client._circuit_breaker.state = CircuitBreaker.OPEN
        client._circuit_breaker._last_failure_time = time.time()
        client._circuit_breaker.recovery_timeout = 9999
        coro = AsyncMock()
        with pytest.raises(ConnectionError, match="Circuit breaker OPEN"):
            await client._call_with_retry(coro)
        coro.assert_not_called()


# ──────────────────────────────────────────────
# NeuralEngineBridge — think_with_authority
# ──────────────────────────────────────────────

class TestNeuralEngineBridge:
    """Tests for NeuralEngineBridge integration logic."""

    def _make_bridge(self, **kwargs):
        mock_client = AsyncMock(spec=NeuralEngineClient)
        mock_client.health_check = AsyncMock(return_value=True)
        mock_client.think = AsyncMock(return_value={
            "content": "test response",
            "thought_process": "reasoning",
            "confidence": 0.9,
            "insights": [],
            "raw_response": "test response",
        })
        mock_client.close = AsyncMock()
        bridge = NeuralEngineBridge(neural_client=mock_client, **kwargs)
        return bridge, mock_client

    @pytest.mark.asyncio
    async def test_think_happy_path_no_dependencies(self):
        """Without GravityWell/CoerciveMemory, request goes straight to client."""
        bridge, client = self._make_bridge()
        request = NeuralRequest(query="test query", require_decision=False)
        response = await bridge.think_with_authority(request)
        assert response.success is True
        assert response.content == "test response"
        assert response.confidence == 0.9
        assert bridge._success_count == 1

    @pytest.mark.asyncio
    async def test_coercive_memory_blocks_request(self):
        """CoerciveMemory DISCOURAGED verdict blocks the request."""
        from enum import Enum

        # Create a real enum to match the production MemoryVerdict
        class FakeVerdict(Enum):
            ALLOWED = "allowed"
            DISCOURAGED = "discouraged"

        mock_memory = MagicMock()
        mock_memory.check.return_value = (FakeVerdict.DISCOURAGED, "blocked for test", 0)

        # Patch the module so the import inside think_with_authority gets our enum
        fake_mod = MagicMock()
        fake_mod.MemoryVerdict = FakeVerdict
        with patch.dict("sys.modules", {"unified_core.core.coercive_memory": fake_mod}):
            bridge, client = self._make_bridge(coercive_memory=mock_memory)
            request = NeuralRequest(query="test")
            response = await bridge.think_with_authority(request)

        assert response.blocked is True
        assert bridge._blocked_count == 1
        client.think.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_check_failure_returns_error(self):
        """If health check fails, response reports the error."""
        bridge, client = self._make_bridge()
        client.health_check.return_value = False
        request = NeuralRequest(query="test", require_decision=False)
        response = await bridge.think_with_authority(request)
        assert response.success is False
        assert "Neural Engine" in response.content
        assert bridge._failure_count == 1

    @pytest.mark.asyncio
    async def test_client_error_inflicts_scar(self):
        """When the neural client raises, ScarTissue.inflict is called."""
        mock_scars = MagicMock()

        # Patch the Failure import
        mock_scar_mod = MagicMock()
        with patch.dict("sys.modules", {"unified_core.core.scar": mock_scar_mod}):
            bridge, client = self._make_bridge(scar_tissue=mock_scars)
            client.health_check.return_value = True
            client.think.side_effect = RuntimeError("LLM crashed")
            request = NeuralRequest(query="test", require_decision=False)
            response = await bridge.think_with_authority(request)

        assert response.success is False
        mock_scars.inflict.assert_called_once()

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Stats correctly track requests, successes, failures."""
        bridge, client = self._make_bridge()

        # 2 successful requests
        for _ in range(2):
            request = NeuralRequest(query="ok", require_decision=False)
            await bridge.think_with_authority(request)

        # 1 failed request
        client.health_check.return_value = False
        request = NeuralRequest(query="fail", require_decision=False)
        await bridge.think_with_authority(request)

        stats = bridge.get_stats()
        assert stats["total_requests"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1

    @pytest.mark.asyncio
    async def test_reason_with_authority_delegates(self):
        """reason_with_authority creates a NeuralRequest and delegates."""
        bridge, client = self._make_bridge()
        response = await bridge.reason_with_authority(
            query="analyze this",
            system_prompt="You are a helper",
            urgency=0.8
        )
        assert response.success is True
        client.think.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_delegates_to_client(self):
        """close() calls neural_client.close()."""
        bridge, client = self._make_bridge()
        await bridge.close()
        client.close.assert_awaited_once()
