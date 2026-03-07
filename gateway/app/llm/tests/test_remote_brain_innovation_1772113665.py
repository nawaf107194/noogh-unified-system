import pytest
from unittest.mock import patch, MagicMock
from gateway.app.llm.remote_brain import RemoteBrain

@pytest.fixture
def remote_brain():
    return RemoteBrain()

@patch('gateway.app.llm.remote_brain.requests.post')
def test_generate_happy_path(mock_post, remote_brain):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"conclusion": "Test response"}
    mock_post.return_value = mock_response

    result = remote_brain.generate("Hello, world!", max_new_tokens=128, temperature=0.7, top_p=0.9)

    assert result == "Test response"
    mock_post.assert_called_once_with(
        "http://example.com/api/v1/process", 
        json={
            "text": "Hello, world!",
            "context": {"max_new_tokens": 128, "temperature": 0.7, "top_p": 0.9},
            "store_memory": False
        }, 
        headers={"X-Internal-Token": "internal_token", "Content-Type": "application/json"}, 
        timeout=32
    )

@patch('gateway.app.llm.remote_brain.requests.post')
def test_generate_edge_cases(mock_post, remote_brain):
    with patch.object(remote_brain, 'neural_engine_url', return_value=None):
        result = remote_brain.generate("Hello, world!", max_new_tokens=128, temperature=0.7, top_p=0.9)
        assert result == "Error: Could not connect to Neural Engine at None"

    mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
    with pytest.raises(requests.exceptions.HTTPError):
        remote_brain.generate("Hello, world!", max_new_tokens=128, temperature=0.7, top_p=0.9)

@patch('gateway.app.llm.remote_brain.requests.post')
def test_generate_error_cases(mock_post, remote_brain):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"conclusion": ""}
    mock_post.return_value = mock_response

    result = remote_brain.generate("Hello, world!", max_new_tokens=128, temperature=0.7, top_p=0.9)
    assert result == ""

@patch('gateway.app.llm.remote_brain.requests.post')
def test_generate_async_behavior(mock_post, remote_brain):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"conclusion": "Test response"}
    mock_post.return_value = mock_response

    import asyncio

    async def async_test():
        result = await remote_brain.generate_async("Hello, world!", max_new_tokens=128, temperature=0.7, top_p=0.9)
        assert result == "Test response"

    asyncio.run(async_test())