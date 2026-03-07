import pytest

class TestDecisionEngineStr:
    def test_str_happy_path(self):
        # Test normal case with all fields populated
        obj = DecisionEngine(metric="accuracy", value=0.95, unit="%")
        assert str(obj) == "accuracy: 0.95%"

    def test_str_empty_unit(self):
        # Test case with empty unit
        obj = DecisionEngine(metric="steps", value=1000, unit="")
        assert str(obj) == "steps: 1000"

    def test_str_zero_value(self):
        # Test boundary case with zero value
        obj = DecisionEngine(metric="error", value=0, unit="Hz")
        assert str(obj) == "error: 0Hz"

    def test_str_negative_value(self):
        # Test boundary case with negative value
        obj = DecisionEngine(metric="temperature", value=-5, unit="C")
        assert str(obj) == "temperature: -5C"

    def test_str_missing_unit(self):
        # Test case where unit is None
        obj = DecisionEngine(metric="count", value=42, unit=None)
        assert str(obj) == "count: 42None"  # None gets converted to string

    def test_str_missing_metric(self):
        # Test case where metric is None
        obj = DecisionEngine(metric=None, value=100, unit="ms")
        assert str(obj) == "None: 100ms"

    def test_str_very_large_value(self):
        # Test boundary case with large value
        obj = DecisionEngine(metric="distance", value=123456789, unit="km")
        assert str(obj) == "distance: 123456789km"