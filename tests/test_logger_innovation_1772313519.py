import pytest
import logging

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            # Initialize the logger with a default configuration
            cls._instance.logger = logging.getLogger('singleton_logger')
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            cls._instance.logger.addHandler(handler)
            cls._instance.logger.setLevel(logging.DEBUG)  # Set your desired default level
        return cls._instance

def test_logger_instance():
    """Test that the Logger returns a singleton instance."""
    logger1 = Logger()
    logger2 = Logger()
    assert logger1 is logger2, "Logger did not return the same instance"

def test_logger_attributes():
    """Test that the Logger has the expected attributes and values."""
    logger = Logger()
    assert hasattr(logger, 'logger'), "Logger does not have a 'logger' attribute"
    assert isinstance(logger.logger, logging.Logger), "Logger's 'logger' is not an instance of logging.Logger"
    handler = logger.logger.handlers[0]
    formatter = handler.formatter
    assert isinstance(handler, logging.StreamHandler), "Logger's handler is not an instance of logging.StreamHandler"
    assert isinstance(formatter, logging.Formatter), "Logger's formatter is not an instance of logging.Formatter"
    assert formatter._fmt == '%(asctime)s - %(name)s - %(levelname)s - %(message)s', "Formatter string does not match expected"

def test_logger_level():
    """Test that the Logger has the correct default level."""
    logger = Logger()
    assert logger.logger.level == logging.DEBUG, "Logger's level is not set to DEBUG"

if __name__ == "__main__":
    pytest.main()