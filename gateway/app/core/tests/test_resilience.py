import pytest
from gateway.app.core.resilience import CircuitState

class TestResilienceInit:

    @pytest.fixture
    def resilience_instance(self):
        from gateway.app.core.resilience import Resilience
        return Resilience

    # Happy path
    def test_happy_path(self, resilience_instance):
        instance = resilience_instance(failure_threshold=5, reset_timeout=120)
        assert instance.failure_threshold == 5
        assert instance.reset_timeout == 120
        assert instance.failure_count == 0
        assert instance.last_failure_time == 0
        assert instance.state == CircuitState.CLOSED

    # Edge cases
    def test_default_values(self, resilience_instance):
        instance = resilience_instance()
        assert instance.failure_threshold == 3
        assert instance.reset_timeout == 60
        assert instance.failure_count == 0
        assert instance.last_failure_time == 0
        assert instance.state == CircuitState.CLOSED

    def test_zero_values(self, resilience_instance):
        instance = resilience_instance(failure_threshold=0, reset_timeout=0)
        assert instance.failure_threshold == 0
        assert instance.reset_timeout == 0
        assert instance.failure_count == 0
        assert instance.last_failure_time == 0
        assert instance.state == CircuitState.CLOSED

    # Error cases
    def test_invalid_failure_threshold(self, resilience_instance):
        with pytest.raises(TypeError):
            resilience_instance(failure_threshold="three")

    def test_invalid_reset_timeout(self, resilience_instance):
        with pytest.raises(TypeError):
            resilience_instance(reset_timeout="sixty")

    # Since there is no async behavior in the __init__ method, we skip testing for async behavior.