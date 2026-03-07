from gateway.app.ml.auto_curriculum import InteractionRecorder
from gateway.app.core.metrics_collector import get_metrics_collector

@pytest.fixture
def recorder():
    return InteractionRecorder()

@pytest.fixture
def mock_collector(mocker):
    collector = mocker.Mock()
    get_metrics_collector.return_value = collector
    return collector

@pytest.mark.parametrize("query, success", [
    ("What is the capital of France?", True),
    ("How old are you?", False)
])
def test_happy_path(recorder, mock_collector, query, success):
    recorder.record_interaction(query, success)
    mock_collector.log_interaction.assert_called_once_with(query, "Response not captured here", success)

def test_empty_query(recorder, mock_collector):
    recorder.record_interaction("", True)
    mock_collector.log_interaction.assert_called_once_with("", "Response not captured here", True)

def test_none_query(recorder, mock_collector):
    recorder.record_interaction(None, False)
    mock_collector.log_interaction.assert_called_once_with(None, "Response not captured here", False)

def test_edge_cases(recorder, mock_collector):
    # Test with boundary conditions if applicable
    recorder.record_interaction("1234567890123456789012345678901234567890", True)
    mock_collector.log_interaction.assert_called_once_with("1234567890123456789012345678901234567890", "Response not captured here", True)

def test_invalid_success_type(recorder, mock_collector):
    recorder.record_interaction("What is your favorite color?", "invalid")
    mock_collector.log_interaction.assert_called_once_with("What is your favorite color?", "Response not captured here", False)