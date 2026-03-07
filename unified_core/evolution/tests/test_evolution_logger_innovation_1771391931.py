import pytest
from unittest.mock import patch, MagicMock
import logging
from unified_core.evolution.evolution_logger import setup_evolution_logging, RequestIdFilter, EVOLUTION_LOG_FORMAT

# Mock the RequestIdFilter and EVOLUTION_LOG_FORMAT for testing purposes
RequestIdFilter = MagicMock()
EVOLUTION_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

@pytest.fixture
def mock_logger():
    with patch('logging.getLogger') as mock_get_logger:
        yield mock_get_logger

@pytest.fixture
def mock_handler():
    with patch('logging.StreamHandler') as mock_stream_handler:
        yield mock_stream_handler

@pytest.fixture
def mock_formatter():
    with patch('logging.Formatter') as mock_formatter:
        yield mock_formatter

@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL])
def test_setup_evolution_logging_happy_path(mock_logger, level):
    # Setup
    evo_logger = mock_logger.return_value
    nb_logger = mock_logger.return_value
    evo_logger.handlers = []
    
    # Call
    result = setup_evolution_logging(level)
    
    # Assert
    assert result == evo_logger
    evo_logger.setLevel.assert_called_once_with(level)
    assert len(evo_logger.handlers) == 1
    evo_logger.addHandler.assert_called_once()
    evo_logger.handlers[0].setFormatter.assert_called_once()
    evo_logger.handlers[0].addFilter.assert_called_once_with(RequestIdFilter.return_value)
    nb_logger.addFilter.assert_called_once_with(RequestIdFilter.return_value)

def test_setup_evolution_logging_existing_handlers(mock_logger):
    # Setup
    evo_logger = mock_logger.return_value
    nb_logger = mock_logger.return_value
    handler1 = MagicMock()
    handler2 = MagicMock()
    evo_logger.handlers = [handler1]
    handler1.filters = []
    handler2.filters = [RequestIdFilter()]
    
    # Call
    result = setup_evolution_logging()
    
    # Assert
    assert result == evo_logger
    handler1.addFilter.assert_called_once_with(RequestIdFilter.return_value)
    handler2.addFilter.assert_not_called()
    nb_logger.addFilter.assert_called_once_with(RequestIdFilter.return_value)

def test_setup_evolution_logging_invalid_level(mock_logger):
    with pytest.raises(TypeError):
        setup_evolution_logging("invalid")

def test_setup_evolution_logging_none_level(mock_logger):
    with pytest.raises(TypeError):
        setup_evolution_logging(None)

def test_setup_evolution_logging_edge_cases(mock_logger):
    # Test with no handlers and no existing filters
    evo_logger = mock_logger.return_value
    nb_logger = mock_logger.return_value
    evo_logger.handlers = []
    
    # Call
    result = setup_evolution_logging(logging.NOTSET)
    
    # Assert
    assert result == evo_logger
    evo_logger.setLevel.assert_called_once_with(logging.NOTSET)
    assert len(evo_logger.handlers) == 1
    evo_logger.addHandler.assert_called_once()
    evo_logger.handlers[0].setFormatter.assert_called_once()
    evo_logger.handlers[0].addFilter.assert_called_once_with(RequestIdFilter.return_value)
    nb_logger.addFilter.assert_called_once_with(RequestIdFilter.return_value)