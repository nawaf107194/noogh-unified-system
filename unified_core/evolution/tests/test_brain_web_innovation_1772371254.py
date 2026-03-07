import pytest

from unified_core.evolution.brain_web import BrainWeb

def test_init_happy_path():
    bw = BrainWeb()
    assert bw.failure_threshold == 3
    assert bw.recovery_time == 300.0
    assert bw.failures == 0
    assert bw.last_failure == 0.0
    assert bw.state == "CLOSED"

def test_init_with_custom_values():
    bw = BrainWeb(failure_threshold=5, recovery_time=600.0)
    assert bw.failure_threshold == 5
    assert bw.recovery_time == 600.0
    assert bw.failures == 0
    assert bw.last_failure == 0.0
    assert bw.state == "CLOSED"

def test_init_with_invalid_failure_threshold():
    with pytest.raises(ValueError):
        BrainWeb(failure_threshold=-1)

def test_init_with_invalid_recovery_time():
    with pytest.raises(ValueError):
        BrainWeb(recovery_time=-1.0)