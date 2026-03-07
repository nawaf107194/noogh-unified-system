import pytest
from unittest.mock import patch

from neural_engine.autonomic_system.dream_processor import DreamProcessor

@pytest.fixture
def dream_processor():
    return DreamProcessor()

def test_stop_dreaming_happy_path(dream_processor):
    """Test the stop_dreaming method with normal inputs."""
    before = dream_processor.is_dreaming
    dream_processor.stop_dreaming()
    after = dream_processor.is_dreaming
    assert not after, "is_dreaming should be False after calling stop_dreaming"
    assert logger.info.call_count == 1, "logger.info should be called once"

def test_stop_dreaming_no_change(dream_processor):
    """Test the stop_dreaming method when is_dreaming is already False."""
    dream_processor.is_dreaming = False
    before = dream_processor.is_dreaming
    dream_processor.stop_dreaming()
    after = dream_processor.is_dreaming
    assert not after, "is_dreaming should remain False"
    assert logger.info.call_count == 0, "logger.info should not be called"

@patch('neural_engine.autonomic_system.dream_processor.logger')
def test_stop_dreaming_logging(mock_logger, dream_processor):
    """Test the stop_dreaming method with logging."""
    before = dream_processor.is_dreaming
    dream_processor.stop_dreaming()
    after = dream_processor.is_dreaming
    assert not after, "is_dreaming should be False after calling stop_dreaming"
    mock_logger.info.assert_called_once_with("Dream mode stopping...")