import pytest

from neural_engine.input_router import InputRouter
from neural_engine.attention_mechanism import AttentionMechanism
from neural_engine.filter_system import FilterSystem
from unittest.mock import patch, mock_open

def test_init_happy_path():
    router = InputRouter()
    assert isinstance(router.attention, AttentionMechanism)
    assert isinstance(router.filters, FilterSystem)
    assert logger.info.call_args_list == [mock.call("InputRouter initialized.")]

@patch('neural_engine.input_router.logger')
def test_init_edge_case_logger_none(mock_logger):
    mock_logger.info = None
    router = InputRouter()
    assert isinstance(router.attention, AttentionMechanism)
    assert isinstance(router.filters, FilterSystem)

@patch('neural_engine.attention_mechanism.AttentionMechanism', side_effect=Exception("Test exception"))
@patch('neural_engine.filter_system.FilterSystem', side_effect=Exception("Test exception"))
def test_init_error_cases(mock_filters, mock_attention):
    with pytest.raises(Exception) as exc_info:
        router = InputRouter()
    assert str(exc_info.value) == "Test exception"