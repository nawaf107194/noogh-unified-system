import pytest

class TestPromotedTargets:
    def test_make_key_happy_path(self):
        # Normal inputs
        file_path = "src/unified_core/evolution/promoted_targets.py"
        function_name = "calculate_metrics"
        expected_key = f"{file_path}:{function_name}"
        assert _make_key(file_path, function_name) == expected_key

    def test_make_key_empty_file_path(self):
        # Edge case: empty file path
        file_path = ""
        function_name = "calculate_metrics"
        expected_key = f"{file_path}:{function_name}"
        assert _make_key(file_path, function_name) == expected_key

    def test_make_key_none_file_path(self):
        # Edge case: None file path
        file_path = None
        function_name = "calculate_metrics"
        with pytest.raises(TypeError):
            _make_key(file_path, function_name)

    def test_make_key_empty_function_name(self):
        # Edge case: empty function name
        file_path = "src/unified_core/evolution/promoted_targets.py"
        function_name = ""
        expected_key = f"{file_path}:{function_name}"
        assert _make_key(file_path, function_name) == expected_key

    def test_make_key_none_function_name(self):
        # Edge case: None function name
        file_path = "src/unified_core/evolution/promoted_targets.py"
        function_name = None
        with pytest.raises(TypeError):
            _make_key(file_path, function_name)

# Import the actual function to be tested
from unified_core.evolution.promoted_targets import _make_key