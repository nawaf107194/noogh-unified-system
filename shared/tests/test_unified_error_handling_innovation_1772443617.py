import pytest

from src.shared.unified_error_handling import UnifiedErrorHandler

class MockLogger:
    def __init__(self):
        self.logs = []

    def error(self, message, exc_info=None):
        self.logs.append((message, exc_info))

@pytest.fixture
def error_handler():
    return UnifiedErrorHandler(MockLogger())

def test_handle_error_happy_path(error_handler):
    error_message = "Something went wrong"
    result = error_handler.handle_error(error_message, context="User input invalid")
    assert result == {"status": "error", "message": error_message, "details": "User input invalid"}
    assert len(error_handler.logger.logs) == 2
    assert error_handler.logger.logs[0][0] == f"Error occurred: {error_message}"
    assert error_handler.logger.logs[1][0] == "Context: User input invalid"

def test_handle_error_no_context(error_handler):
    error_message = "Something went wrong"
    result = error_handler.handle_error(error_message)
    assert result == {"status": "error", "message": error_message, "details": {}}
    assert len(error_handler.logger.logs) == 1
    assert error_handler.logger.logs[0][0] == f"Error occurred: {error_message}"

def test_handle_error_with_none_context(error_handler):
    error_message = "Something went wrong"
    result = error_handler.handle_error(error_message, context=None)
    assert result == {"status": "error", "message": error_message, "details": {}}
    assert len(error_handler.logger.logs) == 1
    assert error_handler.logger.logs[0][0] == f"Error occurred: {error_message}"

def test_handle_error_with_empty_context(error_handler):
    error_message = "Something went wrong"
    result = error_handler.handle_error(error_message, context="")
    assert result == {"status": "error", "message": error_message, "details": ""}
    assert len(error_handler.logger.logs) == 2
    assert error_handler.logger.logs[0][0] == f"Error occurred: {error_message}"
    assert error_handler.logger.logs[1][0] == "Context: "

# Assuming the code does not raise any exceptions for normal inputs, no need for error cases tests

# Async behavior is not applicable since there are no asynchronous operations in the function