import pytest
from unified_core.core.meta_governor import MetaGovernor, WorldModel
import asyncio

class MockAgentDaemon:
    pass

@pytest.fixture
def meta_governor():
    return MetaGovernor()

def test_meta_governor_happy_path(meta_governor):
    assert isinstance(meta_governor.world_model, WorldModel)
    assert meta_governor.daemon is None
    assert meta_governor.id == "meta_governor_aleph"
    assert meta_governor._f_t == 0.0
    assert meta_governor._g_t == 0.0
    assert meta_governor._alpha == 0.2
    assert meta_governor.last_failure_total == 0
    assert meta_governor.last_recalibrate_time == 0
    assert meta_governor.ladder_level == 0
    assert meta_governor._oversight_cycles == 0
    assert isinstance(meta_governor.global_state_lock, asyncio.Lock)
    assert "Meta-Cognitive Supervisor initialized | Governance: v2.1" in caplog.text

def test_meta_governor_with_agent_daemon(meta_governor):
    agent_daemon = MockAgentDaemon()
    mg = MetaGovernor(agent_daemon=agent_daemon)
    assert mg.daemon is agent_daemon
    assert "Meta-Cognitive Supervisor initialized | Governance: v2.1" in caplog.text

def test_meta_governor_invalid_agent_daemon(meta_governor):
    with pytest.raises(TypeError) as e:
        MetaGovernor(agent_daemon=42)
    assert str(e.value) == "Expected agent_daemon to be None or an instance of object, got <class 'int'>"

@pytest.mark.asyncio
async def test_meta_governor_async_behavior(meta_governor):
    async with meta_governor.global_state_lock:
        assert True  # This is a placeholder for actual async behavior tests

def test_meta_governor_logging(caplog):
    caplog.set_level(0)
    mg = MetaGovernor()
    assert "Meta-Cognitive Supervisor initialized | Governance: v2.1" in caplog.text