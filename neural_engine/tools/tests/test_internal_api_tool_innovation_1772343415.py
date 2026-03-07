import pytest
from unittest.mock import patch
from neural_engine.tools.internal_api_tool import InternalAPICaller, NEURAL_ENGINE_BASE, INTERNAL_TOKEN

@patch('neural_engine.tools.internal_api_tool.logger.info')
def test_happy_path(mock_logger):
    caller = InternalAPICaller()
    assert caller.base_url == NEURAL_ENGINE_BASE
    assert caller.headers == {
        "Content-Type": "application/json",
        "X-Internal-Token": INTERNAL_TOKEN
    }
    mock_logger.assert_called_once_with("✅ InternalAPICaller initialized")

def test_edge_case_missing_base_url():
    with patch('neural_engine.tools.internal_api_tool.NEURAL_ENGINE_BASE', None):
        caller = InternalAPICaller()
        assert caller.base_url is None

def test_edge_case_missing_internal_token():
    with patch('neural_engine.tools.internal_api_tool.INTERNAL_TOKEN', None):
        caller = InternalAPICaller()
        assert 'X-Internal-Token' not in caller.headers

def test_error_case_invalid_base_url_type():
    with pytest.raises(TypeError):
        with patch('neural_engine.tools.internal_api_tool.NEURAL_ENGINE_BASE', 12345):
            caller = InternalAPICaller()

def test_error_case_invalid_token_type():
    with pytest.raises(TypeError):
        with patch('neural_engine.tools.internal_api_tool.INTERNAL_TOKEN', 67890):
            caller = InternalAPICaller()