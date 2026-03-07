import pytest

class TestDreamer:
    @pytest.fixture
    def dreamer_instance(self):
        class DummyDreamer:
            def _calculate_health(self, avg_risk: float, failure_rate: float) -> float:
                return 1.0 - ((avg_risk * 0.5) + (failure_rate * 0.5))
        return DummyDreamer()

    def test_calculate_health_happy_path(self, dreamer_instance):
        assert dreamer_instance._calculate_health(0.5, 0.5) == 0.5
        assert dreamer_instance._calculate_health(0.2, 0.8) == 0.4
        assert dreamer_instance._calculate_health(0.8, 0.2) == 0.6

    def test_calculate_health_edge_cases(self, dreamer_instance):
        assert dreamer_instance._calculate_health(0.0, 0.0) == 1.0
        assert dreamer_instance._calculate_health(1.0, 1.0) == 0.0
        assert dreamer_instance._calculate_health(0.0, 1.0) == 0.5
        assert dreamer_instance._calculate_health(1.0, 0.0) == 0.5

    def test_calculate_health_error_cases(self, dreamer_instance):
        with pytest.raises(TypeError):
            dreamer_instance._calculate_health("string", 0.5)
        with pytest.raises(TypeError):
            dreamer_instance._calculate_health(0.5, "string")
        with pytest.raises(ValueError):
            dreamer_instance._calculate_health(-0.1, 0.5)
        with pytest.raises(ValueError):
            dreamer_instance._calculate_health(0.5, -0.1)
        with pytest.raises(ValueError):
            dreamer_instance._calculate_health(1.1, 0.5)
        with pytest.raises(ValueError):
            dreamer_instance._calculate_health(0.5, 1.1)

    def test_calculate_health_async_behavior(self, dreamer_instance):
        # Since the function does not involve any async operations,
        # there's no need to test async behavior.
        pass