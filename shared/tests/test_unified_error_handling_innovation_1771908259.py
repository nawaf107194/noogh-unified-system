import pytest

class MockLogger:
    def error(self, message, exc_info=None):
        pass

@pytest.fixture
def logger():
    return MockLogger()

class TestUnifiedErrorHandler:
    def test_happy_path(self, logger):
        handler = UnifiedErrorHandler(logger)
        error = Exception("Test error")
        result = handler.handle_error(error, context="test context")
        assert result == {
            "status": "error",
            "message": str(error),
            "details": {"context": "test context"}
        }

    def test_empty_context(self, logger):
        handler = UnifiedErrorHandler(logger)
        error = Exception("Test error")
        result = handler.handle_error(error)
        assert result == {
            "status": "error",
            "message": str(error),
            "details": {}
        }

    def test_none_inputs(self, logger):
        handler = UnifiedErrorHandler(logger)
        result = handler.handle_error(None, context=None)
        assert result is None

    def test_invalid_context_type(self, logger):
        handler = UnifiedErrorHandler(logger)
        error = Exception("Test error")
        with pytest.raises(TypeError) as exc_info:
            handler.handle_error(error, context=123)
        assert str(exc_info.value) == "Invalid context type: <class 'int'>"

    def test_logging_with_context(self, logger):
        handler = UnifiedErrorHandler(logger)
        error = Exception("Test error")
        handler.handle_error(error, context="test context")
        # Assuming the MockLogger records the log entries somewhere
        assert hasattr(handler.logger, "log_entries")
        assert len(handler.logger.log_entries) == 2

    def test_logging_without_context(self, logger):
        handler = UnifiedErrorHandler(logger)
        error = Exception("Test error")
        handler.handle_error(error)
        # Assuming the MockLogger records the log entries somewhere
        assert hasattr(handler.logger, "log_entries")
        assert len(handler.logger.log_entries) == 1

class UnifiedErrorHandler:
    def __init__(self, logger):
        self.logger = logger
        if not isinstance(self.logger, MockLogger):
            raise ValueError("logger must be an instance of MockLogger")

    def handle_error(self, error, context=None):
        """
        Handles an error by logging it and optionally including context.
        
        :param error: The error instance to be handled.
        :param context: Additional context information to include in the log.
        """
        # Log the error with the full traceback
        self.logger.error(f"Error occurred: {str(error)}", exc_info=True)
        
        if context:
            self.logger.error(f"Context: {context}")
        
        # Optionally, you can return a formatted error response for APIs
        return {
            "status": "error",
            "message": str(error),
            "details": context if context else {}
        }