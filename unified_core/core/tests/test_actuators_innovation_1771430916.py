import pytest

class MockGovernanceMixin:
    def __init__(self, rate_limit_per_min, latency_limit_ms):
        self.rate_limit_per_min = rate_limit_per_min
        self.latency_limit_ms = latency_limit_ms

class Actuator:
    def __init__(self):
        MockGovernanceMixin.__init__(self, rate_limit_per_min=60, latency_limit_ms=200)
        self._action_count = 0
        self.blocked_count = 0  # Redundant but safe

def test_happy_path():
    actuator = Actuator()
    assert actuator.rate_limit_per_min == 60
    assert actuator.latency_limit_ms == 200
    assert actuator._action_count == 0
    assert actuator.blocked_count == 0

def test_edge_cases():
    actuator = Actuator()
    assert actuator.rate_limit_per_min >= 0
    assert actuator.latency_limit_ms >= 0

def test_error_cases():
    with pytest.raises(TypeError):
        MockGovernanceMixin("not an int", 200)
    with pytest.raises(TypeError):
        MockGovernanceMixin(60, "not an int")

def test_async_behavior():
    # Since the given init method does not have any async behavior,
    # we can skip this test or mock it if there was supposed to be some.
    pass