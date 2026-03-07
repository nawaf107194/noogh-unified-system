import pytest
from datetime import datetime
from unittest.mock import patch

@pytest.fixture
def action_executor():
    class MockActionExecutor:
        def __init__(self):
            self.logger = MockLogger()

        def _log_error(self, params: dict) -> dict:
            message = params.get("message", "")
            self.logger.error(f"🔴 {message}")
            return {
                "action": "log_error",
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "message": f"Logged error: {message}"
            }
    
    class MockLogger:
        def __init__(self):
            self.error_messages = []

        def error(self, msg):
            self.error_messages.append(msg)

    return MockActionExecutor()

def test_log_error_happy_path(action_executor):
    params = {"message": "An error occurred"}
    result = action_executor._log_error(params)
    assert result["action"] == "log_error"
    assert result["success"]
    assert "Logged error: An error occurred" in result["message"]
    assert len(result["timestamp"]) > 0

def test_log_error_empty_message(action_executor):
    params = {"message": ""}
    result = action_executor._log_error(params)
    assert result["action"] == "log_error"
    assert result["success"]
    assert "Logged error: " in result["message"]

def test_log_error_none_message(action_executor):
    params = {"message": None}
    result = action_executor._log_error(params)
    assert result["action"] == "log_error"
    assert result["success"]
    assert "Logged error: None" in result["message"]

def test_log_error_missing_message_key(action_executor):
    params = {}
    result = action_executor._log_error(params)
    assert result["action"] == "log_error"
    assert result["success"]
    assert "Logged error: " in result["message"]

def test_log_error_invalid_input_type(action_executor):
    with pytest.raises(TypeError):
        action_executor._log_error("not a dictionary")

@patch('datetime.datetime')
def test_log_error_with_mocked_datetime(mock_datetime, action_executor):
    mock_datetime.now.return_value.isoformat.return_value = 'mocked-isoformat'
    params = {"message": "An error occurred"}
    result = action_executor._log_error(params)
    assert result["timestamp"] == 'mocked-isoformat'

def test_logger_called_with_correct_message(action_executor):
    params = {"message": "An error occurred"}
    action_executor._log_error(params)
    assert action_executor.logger.error_messages == ["🔴 An error occurred"]