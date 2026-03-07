import pytest
from unittest.mock import patch
from neural_engine.neural_engine_logging import logger

@patch('neural_engine.autonomic_system.event_stream.get_event_stream')
def test_self_awareness_adapter_init_happy_path(mock_get_event_stream):
    """Test the happy path for __init__"""
    # Arrange
    mock_get_event_stream.return_value = "mock event stream"
    
    # Act
    adapter = self_awareness_adapter.SelfAwarenessAdapter()
    
    # Assert
    assert adapter.stream == "mock event stream"
    assert adapter.analysis_history == []
    assert len(logger.info.call_args_list) == 1
    logger.info.assert_called_with("✅ SelfAwarenessAdapter initialized")

def test_self_awareness_adapter_init_edge_case_none():
    """Test the edge case where get_event_stream returns None"""
    # Arrange
    with patch('neural_engine.autonomic_system.event_stream.get_event_stream', return_value=None):
        # Act
        adapter = self_awareness_adapter.SelfAwarenessAdapter()
        
        # Assert
        assert adapter.stream is None
        assert adapter.analysis_history == []
        assert len(logger.info.call_args_list) == 1
        logger.info.assert_called_with("✅ SelfAwarenessAdapter initialized")

def test_self_awareness_adapter_init_edge_case_empty():
    """Test the edge case where get_event_stream returns an empty string"""
    # Arrange
    with patch('neural_engine.autonomic_system.event_stream.get_event_stream', return_value=""):
        # Act
        adapter = self_awareness_adapter.SelfAwarenessAdapter()
        
        # Assert
        assert adapter.stream == ""
        assert adapter.analysis_history == []
        assert len(logger.info.call_args_list) == 1
        logger.info.assert_called_with("✅ SelfAwarenessAdapter initialized")

def test_self_awareness_adapter_init_error_case_invalid_input():
    """Test the edge case where get_event_stream raises an error"""
    # Arrange
    with patch('neural_engine.autonomic_system.event_stream.get_event_stream', side_effect=Exception("Invalid input")):
        # Act & Assert
        with pytest.raises(Exception, match="Invalid input"):
            adapter = self_awareness_adapter.SelfAwarenessAdapter()