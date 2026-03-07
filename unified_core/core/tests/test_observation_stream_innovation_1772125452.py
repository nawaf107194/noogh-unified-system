import pytest
from unittest.mock import patch, MagicMock
from unified_core.core.observation_stream import ObservationStream, Signal

@patch('os.getloadavg')
def test_get_load_signals_happy_path(mock_getloadavg):
    mock_getloadavg.return_value = (0.1, 0.2, 0.3)
    observation_stream = ObservationStream()
    signals = observation_stream._get_load_signals()
    
    assert len(signals) == 1
    assert signals[0].name == "load_average_1m"
    assert signals[0].value == 0.1
    assert signals[0].source == "os"
    assert signals[0].unit == "load"

@patch('os.getloadavg')
def test_get_load_signals_empty_result(mock_getloadavg):
    mock_getloadavg.return_value = (None, None, None)
    observation_stream = ObservationStream()
    signals = observation_stream._get_load_signals()
    
    assert len(signals) == 0

@patch('os.getloadavg')
def test_get_load_signals_error_case(mock_getloadavg):
    mock_getloadavg.side_effect = OSError("Failed to get load averages")
    observation_stream = ObservationStream()
    signals = observation_stream._get_load_signals()
    
    assert len(signals) == 0