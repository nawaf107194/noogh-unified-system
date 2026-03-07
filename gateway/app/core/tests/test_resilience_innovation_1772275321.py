import pytest

from gateway.app.core.resilience import CircuitState, Resilience

class TestResilience:

    def test_happy_path(self):
        # Normal inputs
        resilience = Resilience(failure_threshold=3, reset_timeout=60)
        assert resilience.failure_threshold == 3
        assert resilience.reset_timeout == 60
        assert resilience.failure_count == 0
        assert resilience.last_failure_time == 0
        assert resilience.state == CircuitState.CLOSED

    def test_edge_cases(self):
        # Empty inputs (not applicable here)
        resilience = Resilience()
        assert resilience.failure_threshold == 3
        assert resilience.reset_timeout == 60
        assert resilience.failure_count == 0
        assert resilience.last_failure_time == 0
        assert resilience.state == CircuitState.CLOSED

    def test_error_cases(self):
        # Invalid inputs (not applicable here)
        with pytest.raises(TypeError):
            Resilience(failure_threshold="3", reset_timeout=60)

    def test_async_behavior(self):
        # Async behavior (not applicable here)
        pass