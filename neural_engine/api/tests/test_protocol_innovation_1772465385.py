import pytest

class TestValidateAction:
    @pytest.mark.parametrize("input_value, expected_output", [
        ("ExecuteCode", "ExecuteCode"),
        ("ExecuteShell", "ExecuteShell"),
        ("ShellExecutor", "ShellExecutor"),
        ("RecallMemory", "RecallMemory"),
        ("StoreMemory", "StoreMemory"),
        ("Dream", "Dream")
    ])
    def test_happy_path(self, input_value, expected_output):
        assert validate_action(input_value) == expected_output

    @pytest.mark.parametrize("input_value", [
        "",
        None,
        [],
        {},
        123,
        True,
        "UnknownAction"
    ])
    def test_error_cases(self, input_value):
        with pytest.raises(ValueError):
            validate_action(input_value)