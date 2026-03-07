import pytest
from unified_core.evolution.brain_web import CircuitBreaker

def test_record_failure_happy_path():
    cb = CircuitBreaker(failure_threshold=2, recovery_time=10)
    cb.record_failure()
    assert cb.failures == 1
    assert cb.last_failure is not None
    assert cb.state == "CLOSED"

def test_record_failure_edge_case_max_failures():
    cb = CircuitBreaker(failure_threshold=3, recovery_time=10)
    for _ in range(3):
        cb.record_failure()
    assert cb.failures == 3
    assert cb.last_failure is not None
    assert cb.state == "OPEN"

def test_record_failure_edge_case_initial_state():
    cb = CircuitBreaker(failure_threshold=2, recovery_time=10)
    assert cb.failures == 0
    assert cb.last_failure is None
    assert cb.state == "CLOSED"

def test_record_failure_error_case_negative_threshold():
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=-1, recovery_time=10)

def test_record_failure_error_case_negative_recovery_time():
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=2, recovery_time=-1)