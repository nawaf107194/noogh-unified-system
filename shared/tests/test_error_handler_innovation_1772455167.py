import pytest
from unittest.mock import MagicMock
import logging
from src.shared.error_handler import ErrorHandler

def test_init_with_logger():
    logger = MagicMock()
    handler = ErrorHandler(logger=logger)
    assert handler.logger == logger

def test_init_without_logger():
    handler = ErrorHandler()
    assert isinstance(handler.logger, logging.Logger)

def test_init_with_none_logger():
    handler = ErrorHandler(logger=None)
    assert isinstance(handler.logger, logging.Logger)

def test_init_with_empty_string_logger_name():
    handler = ErrorHandler(logger='')
    assert isinstance(handler.logger, logging.Logger)

# Edge cases and error cases are not applicable here as the function does not explicitly raise any exceptions