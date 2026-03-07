import pytest

from noogh.utils.error_handler_1771345059 import get_error_handler, LoggingErrorHandler, AlertingErrorHandler

class TestGetErrorHandler:
    def test_happy_path_logging(self):
        error_handler = get_error_handler('logging')
        assert isinstance(error_handler, LoggingErrorHandler)

    def test_happy_path_alerting(self):
        error_handler = get_error_handler('alerting')
        assert isinstance(error_handler, AlertingErrorHandler)

    def test_edge_case_empty_input(self):
        with pytest.raises(ValueError) as excinfo:
            get_error_handler('')
        assert "Unknown error handler type" in str(excinfo.value)

    def test_edge_case_none_input(self):
        with pytest.raises(ValueError) as excinfo:
            get_error_handler(None)
        assert "Unknown error handler type" in str(excinfo.value)

    def test_error_case_invalid_input(self):
        with pytest.raises(ValueError) as excinfo:
            get_error_handler('invalid_type')
        assert "Unknown error handler type" in str(excinfo.value)