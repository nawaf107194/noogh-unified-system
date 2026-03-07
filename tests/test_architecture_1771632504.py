import pytest

class TestExecuteFunction:

    def test_happy_path(self):
        # Happy path: normal inputs
        data = 5
        result = execute(data)
        assert result == 10, f"Expected 10 but got {result}"

    def test_edge_case_none(self):
        # Edge case: None input
        data = None
        result = execute(data)
        assert result is None, f"Expected None but got {result}"

    def test_edge_case_empty_string(self):
        # Edge case: empty string input
        data = ""
        result = execute(data)
        assert result == "", f"Expected '' but got '{result}'"

    def test_edge_case_negative_number(self):
        # Edge case: negative number input
        data = -3
        result = execute(data)
        assert result == -6, f"Expected -6 but got {result}"

    def test_error_case_non_numeric_input(self):
        # Error case: non-numeric input (assuming the function should handle this gracefully)
        data = "abc"
        result = execute(data)
        assert result is None or result == "", f"Unexpected result for non-numeric input: {result}"