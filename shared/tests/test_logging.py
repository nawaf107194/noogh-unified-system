import pytest
import logging

class TestLoggerInit:

    @pytest.fixture
    def logger_instance(self):
        from shared.logging import Logger  # Assuming the class is named Logger
        return Logger

    def test_happy_path(self, logger_instance):
        """Test with a normal input."""
        name = "test_logger"
        logger = logger_instance(name)
        assert logger.logger.name == name
        assert logger.logger.level == logging.DEBUG

    def test_empty_string(self, logger_instance):
        """Test with an empty string."""
        name = ""
        logger = logger_instance(name)
        assert logger.logger.name == name
        assert logger.logger.level == logging.DEBUG

    def test_none_name(self, logger_instance):
        """Test with None as the name."""
        name = None
        logger = logger_instance(name)
        assert logger.logger.name == "root"  # Default root logger if name is None
        assert logger.logger.level == logging.DEBUG

    def test_invalid_input_type(self, logger_instance):
        """Test with an invalid input type."""
        with pytest.raises(TypeError):
            logger_instance(123)  # Passing an integer should raise TypeError

    def test_async_behavior(self, logger_instance):
        """Test to check if async behavior is required or not.
           Since logging is synchronous, no specific async test is needed."""
        pass