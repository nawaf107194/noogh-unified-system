import pytest
from unified_core.core.meta_governor import MetaGovernor
from unified_core.core.world_model import WorldModel

def test_happy_path():
    agent_daemon = object()
    meta_governor = MetaGovernor(agent_daemon)
    assert isinstance(meta_governor, MetaGovernor)
    assert meta_governor.world_model is not None
    assert meta_governor.daemon is agent_daemon
    assert meta_governor.id == "meta_governor_aleph"
    assert meta_governor._f_t == 0.0
    assert meta_governor._g_t == 0.0
    assert meta_governor._alpha == 0.2
    assert meta_governor.last_failure_total == 0
    assert meta_governor.last_recalibrate_time == 0
    assert meta_governor.ladder_level == 0
    assert meta_governor._oversight_cycles == 0
    assert isinstance(meta_governor.global_state_lock, asyncio.Lock)
    assert logger.info.call_args_list[-1][0] == ("Meta-Cognitive Supervisor initialized | Governance: v2.1",)

def test_edge_case_none():
    agent_daemon = None
    meta_governor = MetaGovernor(agent_daemon)
    assert isinstance(meta_governor, MetaGovernor)
    assert meta_governor.world_model is not None
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
    assert logger.info.call_args_list[-1][0] == ("Meta-Cognitive Supervisor initialized | Governance: v2.1",)

def test_error_case_invalid_type():
    agent_daemon = "not_an_object"
    with pytest.raises(TypeError) as exc_info:
        MetaGovernor(agent_daemon)
    assert str(exc_info.value) == "Expected agent_daemon to be None or an instance of object, got <class 'str'>"

def test_async_behavior():
    agent_daemon = object()
    meta_governor = MetaGovernor(agent_daemon)
    async def test_lock():
        async with meta_governor.global_state_lock:
            pass
    pytest.run_coroutine(test_lock())