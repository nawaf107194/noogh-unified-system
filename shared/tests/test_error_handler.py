import logging
from noogh_unified_system.src.shared.error_handler import ErrorHandler

def test_init_with_default_logger():
    handler = ErrorHandler()
    assert isinstance(handler.logger, logging.Logger)
    assert handler.logger.name == "error_handler"

def test_init_with_custom_logger():
    custom_logger = logging.getLogger("custom")
    handler = ErrorHandler(custom_logger)
    assert handler.logger is custom_logger