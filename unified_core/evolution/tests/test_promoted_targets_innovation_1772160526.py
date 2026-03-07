import pytest

from unified_core.evolution.promoted_targets import get_promoted_targets, PromotedTargets

class TestGetPromotedTargets:

    def test_happy_path(self):
        """Test normal inputs."""
        result = get_promoted_targets()
        assert isinstance(result, PromotedTargets)
        assert result is PromotedTargets.get_instance()

    def test_edge_cases_none(self):
        """Test None input."""
        with pytest.raises(TypeError) as exc_info:
            get_promoted_targets(None)
        assert "NoneType" in str(exc_info.value)

    def test_edge_cases_empty(self):
        """Test empty input."""
        with pytest.raises(ValueError) as exc_info:
            get_promoted_targets("")
        assert "empty" in str(exc_info.value)

    def test_error_case_invalid_input(self):
        """Test invalid inputs."""
        with pytest.raises(TypeError) as exc_info:
            get_promoted_targets(42)
        assert "int" in str(exc_info.value)

    def test_async_behavior(self):
        """Test async behavior if applicable (not applicable for this function)."""
        pass