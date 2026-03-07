import pytest

from shared.unified_error_handling import UnifiedErrorHandler

class MockLogger:
    def error(self, message, exc_info=None):
        self.message = message
        self.exc_info = exc_info

@pytest.fixture
def error_handler():
    return UnifiedErrorHandler(MockLogger())

def test_handle_error_happy_path(error_handler):
    error = Exception("Test Error")
    context = "Test Context"
    
    result = error_handler.handle_error(error, context)
    
    assert error_handler.logger.message == "Error occurred: Test Error"
    assert error_handler.logger.exc_info
    assert result == {
        "status": "error",
        "message": str(error),
        "details": context
    }

def test_handle_error_no_context(error_handler):
    error = Exception("Test Error")
    
    result = error_handler.handle_error(error)
    
    assert error_handler.logger.message == "Error occurred: Test Error"
    assert error_handler.logger.exc_info
    assert result == {
        "status": "error",
        "message": str(error),
        "details": {}
    }

def test_handle_error_empty_context(error_handler):
    error = Exception("Test Error")
    context = ""
    
    result = error_handler.handle_error(error, context)
    
    assert error_handler.logger.message == "Error occurred: Test Error"
    assert error_handler.logger.exc_info
    assert result == {
        "status": "error",
        "message": str(error),
        "details": ""
    }

def test_handle_error_none_context(error_handler):
    error = Exception("Test Error")
    context = None
    
    result = error_handler.handle_error(error, context)
    
    assert error_handler.logger.message == "Error occurred: Test Error"
    assert error_handler.logger.exc_info
    assert result == {
        "status": "error",
        "message": str(error),
        "details": {}
    }

def test_handle_error_none_error(error_handler):
    error = None
    context = "Test Context"
    
    result = error_handler.handle_error(error, context)
    
    assert not hasattr(error_handler.logger, 'message')
    assert not hasattr(error_handler.logger, 'exc_info')
    assert result is None

def test_handle_error_empty_string_error(error_handler):
    error = ""
    context = "Test Context"
    
    result = error_handler.handle_error(error, context)
    
    assert error_handler.logger.message == "Error occurred: "
    assert error_handler.logger.exc_info
    assert result == {
        "status": "error",
        "message": str(error),
        "details": context
    }