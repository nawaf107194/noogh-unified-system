import pytest

from gateway.app.core.validation import wrapper, validate_auth_context, validate_tool_args
from validation_error import ValidationError

class MockGateway:
    def __call__(self, tool_name, *args, **kwargs):
        return f"Tool {tool_name} executed with args: {args}, kwargs: {kwargs}"

@pytest.fixture
def mock_gateway():
    return MockGateway()

def test_happy_path(mock_gateway):
    result = wrapper(mock_gateway, "test_tool", arg1="value1", arg2="value2")
    assert result == "Tool test_tool executed with args: ('value1', 'value2'), kwargs: {}"

def test_empty_auth(mock_gateway):
    result = wrapper(mock_gateway, "test_tool", auth=None)
    assert result == "Tool test_tool executed with args: (), kwargs: {}"

def test_invalid_auth(mock_gateway):
    validate_auth_context = lambda x: False
    with pytest.raises(ValidationError) as e:
        wrapper(mock_gateway, "test_tool", auth="invalid")
    assert str(e.value) == "Invalid auth context"

def test_empty_tool_args(mock_gateway):
    result = wrapper(mock_gateway, "test_tool", arg1="", arg2="")
    assert result == "Tool test_tool executed with args: ('', ''), kwargs: {}"

def test_invalid_tool_args(mock_gateway):
    validate_tool_args = lambda tool_name, args: False
    with pytest.raises(ValidationError) as e:
        wrapper(mock_gateway, "test_tool", arg1="value1")
    assert str(e.value) == "Invalid tool arguments for test_tool"