import pytest
from neural_engine.autonomic_system.initiative_loop import InitiativeLoop
import threading

@pytest.fixture
def mock_thread():
    return threading.Thread()

class MockSystemAdminAdapter:
    def reset(self):
        pass

class MockPolicyEngine:
    def assess(self, observations):
        return []

class MockActionExecutor:
    def execute(self, proposals):
        pass

class MockEventStream:
    def get_observations(self):
        return []

def test_happy_path():
    loop = InitiativeLoop(interval=60)
    assert loop.adapter is not None
    assert loop.policy is not None
    assert loop.executor is not None
    assert loop.stream is not None
    assert loop.interval == 60
    assert loop.running is False
    assert loop.thread is None
    assert loop.stats == {
        "observations": 0,
        "assessments": 0,
        "proposals": 0,
        "executions": 0,
        "blocked": 0
    }
    assert logger.info.call_args_list[-1] == pytest.approx(("✅ InitiativeLoop initialized (interval=60s)",))

def test_edge_case_interval_none():
    loop = InitiativeLoop(interval=None)
    assert loop.interval == 60

def test_edge_case_interval_empty_string():
    loop = InitiativeLoop(interval="")
    assert loop.interval == 60

def test_async_behavior(mocker, mock_thread):
    mocker.patch('threading.Thread', return_value=mock_thread)
    
    loop = InitiativeLoop(interval=60)
    assert loop.thread is not None
    loop.start()
    loop.stop()