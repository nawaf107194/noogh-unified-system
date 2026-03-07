from gateway.app.core.validation import validate_tool_execution, ValidationError
from unittest.mock import patch

def dummy_function(self, tool_name: str, **kwargs):
    return {"success": True, "error": "", "output": kwargs}

@validate_tool_execution
def execute_tool(self, tool_name: str, **kwargs):
    return dummy_function(self, tool_name, **kwargs)

class TestValidateToolExecution:
    @pytest.fixture
    def execution_func(self):
        return execute_tool

    def test_happy_path(self, execution_func):
        result = execution_func(None, "tool1", param1="value1")
        assert result == {"success": True, "error": "", "output": {'param1': 'value1'}}

    @patch('gateway.app.core.validation.validate_auth_context')
    def test_with_auth(self, mock_validate_auth_context, execution_func):
        result = execution_func(None, "tool1", auth={"token": "abc123"}, param1="value1")
        assert result == {"success": True, "error": "", "output": {'param1': 'value1'}}
        mock_validate_auth_context.assert_called_once_with({"token": "abc123"})

    def test_empty_tool_name(self, execution_func):
        result = execution_func(None, "", param1="value1")
        assert result == {"success": False, "error": "Validation error: Tool name cannot be empty", "output": ""}

    def test_missing_auth_param(self, execution_func):
        result = execution_func(None, "tool1", auth=None, param1="value1")
        assert result == {"success": False, "error": "Validation error: Invalid authentication context provided", "output": ""}

    def test_invalid_tool_args(self, execution_func):
        with pytest.raises(ValidationError) as exc_info:
            execute_tool(None, "tool2", invalid_arg="value1")
        assert str(exc_info.value).startswith("Invalid arguments for tool 'tool2': Invalid argument 'invalid_arg'")

    @patch('gateway.app.core.validation.validate_auth_context', side_effect=ValidationError("Auth validation failed"))
    def test_auth_validation_failure(self, mock_validate_auth_context, execution_func):
        result = execution_func(None, "tool1", auth={"token": "abc123"}, param1="value1")
        assert result == {"success": False, "error": "Validation error: Auth validation failed", "output": ""}

    def test_no_output_on_success(self, execution_func):
        result = execution_func(None, "tool1", param1="value1")
        assert 'output' not in result

    def test_error_output_on_failure(self, execution_func):
        with pytest.raises(ValidationError) as exc_info:
            execute_tool(None, "tool2", invalid_arg="value1")
        error_message = str(exc_info.value)
        assert f"Validation error: Invalid arguments for tool 'tool2': Invalid argument 'invalid_arg'" in error_message