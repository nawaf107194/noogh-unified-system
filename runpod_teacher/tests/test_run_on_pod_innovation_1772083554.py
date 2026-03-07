import pytest
from runpod_teacher.run_on_pod import call_teacher

@pytest.fixture
def mock_requests_post(mocker):
    def mock_response(status_code=200, json_data=None):
        resp = mocker.Mock()
        resp.raise_for_status = lambda: None if status_code == 200 else Exception(f"Mocked HTTP {status_code} error")
        resp.json.return_value = json_data
        return resp

    post_mock = mocker.patch("requests.post", side_effect=mock_response)
    yield post_mock

def test_happy_path(mock_requests_post):
    response_data = {
        "choices": [{"message": {"content": "Hello, world!"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5}
    }
    mock_requests_post.return_value.json.return_value = response_data

    result = call_teacher(messages=[{"role": "user", "content": "Hi there"}])

    assert result == {
        "content": "Hello, world!",
        "input_tokens": 10,
        "output_tokens": 5,
        "latency_ms": pytest.approx(1200),  # Approximate due to time.sleep not being patched
        "success": True
    }

def test_edge_case_empty_messages(mock_requests_post):
    mock_requests_post.return_value.json.return_value = {}

    result = call_teacher(messages=[])

    assert result == {
        "content": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "latency_ms": pytest.approx(1200),  # Approximate due to time.sleep not being patched
        "success": False,
        "error": "Request failed with status code: 400"
    }

def test_edge_case_none_messages(mock_requests_post):
    mock_requests_post.return_value.json.return_value = {}

    result = call_teacher(messages=None)

    assert result == {
        "content": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "latency_ms": pytest.approx(1200),  # Approximate due to time.sleep not being patched
        "success": False,
        "error": "Request failed with status code: 400"
    }

def test_edge_case_boundary_max_tokens(mock_requests_post):
    response_data = {
        "choices": [{"message": {"content": "Hello, world!"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5}
    }
    mock_requests_post.return_value.json.return_value = response_data

    result = call_teacher(messages=[{"role": "user", "content": "Hi there"}], max_tokens=4096)

    assert result == {
        "content": "Hello, world!",
        "input_tokens": 10,
        "output_tokens": 5,
        "latency_ms": pytest.approx(1200),  # Approximate due to time.sleep not being patched
        "success": True
    }

def test_error_case_invalid_input(mock_requests_post):
    mock_requests_post.side_effect = Exception("Invalid input error")

    result = call_teacher(messages=[{"role": "user", "content": "Hi there"}])

    assert result == {
        "content": "",
        "success": False,
        "error": "Invalid input error"
    }