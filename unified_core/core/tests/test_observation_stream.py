import pytest
from unittest.mock import MagicMock

class TestObservationStream:
    @pytest.fixture
    def observation_stream(self):
        from unified_core.core.observation_stream import ObservationStream
        return ObservationStream()

    @pytest.fixture
    def mock_signal_collector(self):
        class MockSignalCollector:
            def __init__(self, name="Test Collector"):
                self.name = name
        return MockSignalCollector()

    def test_add_collector_happy_path(self, observation_stream, mock_signal_collector):
        # Arrange
        initial_length = len(observation_stream._collectors)
        
        # Act
        observation_stream.add_collector(mock_signal_collector)
        
        # Assert
        assert len(observation_stream._collectors) == initial_length + 1
        assert observation_stream._collectors[-1] is mock_signal_collector

    def test_add_collector_with_none(self, observation_stream):
        # Arrange
        initial_length = len(observation_stream._collectors)
        
        # Act & Assert
        with pytest.raises(TypeError):
            observation_stream.add_collector(None)
        assert len(observation_stream._collectors) == initial_length

    def test_add_collector_with_invalid_type(self, observation_stream):
        # Arrange
        initial_length = len(observation_stream._collectors)
        
        # Act & Assert
        with pytest.raises(TypeError):
            observation_stream.add_collector("Invalid Type")
        assert len(observation_stream._collectors) == initial_length

    def test_add_collector_with_empty_collector_list(self, observation_stream, mock_signal_collector):
        # Arrange
        assert not observation_stream._collectors
        
        # Act
        observation_stream.add_collector(mock_signal_collector)
        
        # Assert
        assert len(observation_stream._collectors) == 1
        assert observation_stream._collectors[0] is mock_signal_collector

    def test_add_collector_with_logger_info(self, observation_stream, mock_signal_collector):
        # Arrange
        logger_mock = MagicMock()
        observation_stream.logger = logger_mock
        
        # Act
        observation_stream.add_collector(mock_signal_collector)
        
        # Assert
        logger_mock.info.assert_called_once_with(f"Added collector: {mock_signal_collector.name}")