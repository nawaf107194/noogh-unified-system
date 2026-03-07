import pytest
from unittest.mock import MagicMock

class TestErrorHandler:
    @pytest.fixture
    def error_handler_instance(self):
        class ErrorHandler:
            def __init__(self):
                self.error_log = []
            
            def log_error(self, error_message):
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.error_log.append(f"{timestamp} - {error_message}")
                print(f"Error logged: {error_message}")
        
        return ErrorHandler()

    def test_happy_path(self, error_handler_instance):
        error_handler_instance.log_error = MagicMock()
        error_handler_instance.log_error("Test error message")
        assert len(error_handler_instance.error_log) == 1
        assert "Test error message" in error_handler_instance.error_log[0]

    def test_empty_string(self, error_handler_instance):
        error_handler_instance.log_error = MagicMock()
        error_handler_instance.log_error("")
        assert len(error_handler_instance.error_log) == 1
        assert " - " in error_handler_instance.error_log[0]

    def test_none_input(self, error_handler_instance):
        with pytest.raises(TypeError):
            error_handler_instance.log_error(None)

    def test_invalid_input_type(self, error_handler_instance):
        with pytest.raises(AttributeError):
            error_handler_instance.log_error(123)

    def test_boundary_conditions(self, error_handler_instance):
        long_error_message = "a" * 5000
        error_handler_instance.log_error = MagicMock()
        error_handler_instance.log_error(long_error_message)
        assert len(error_handler_instance.error_log) == 1
        assert long_error_message in error_handler_instance.error_log[0]