import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def filter_system():
    from neural_engine.filter_system import FilterSystem
    return FilterSystem()

def test_init_happy_path(filter_system):
    assert "FilterSystem initialized." in caplog.text

@patch('neural_engine.filter_system.logger')
def test_init_edge_case_none(mock_logger):
    mock_filter_system = type(filter_system)()
    mock_logger.info.assert_called_once_with("FilterSystem initialized.")

@patch('neural_engine.filter_system.logger')
def test_init_edge_case_empty_string(mock_logger):
    mock_filter_system = type(filter_system)("")
    mock_logger.info.assert_called_once_with("FilterSystem initialized.")

@patch('neural_engine.filter_system.logger')
def test_init_error_case_invalid_input(mock_logger):
    with pytest.raises(TypeError):
        mock_filter_system = type(filter_system)(123)