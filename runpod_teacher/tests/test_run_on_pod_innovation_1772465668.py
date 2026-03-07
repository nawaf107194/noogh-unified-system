import pytest
from runpod_teacher.run_on_pod import call_teacher
import requests

class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self.json_data = json_data
    
    def json(self):
        return self.json_data

@pytest.fixture
def mock_requests_post(monkeypatch):
    def mock_post(url, json=None, timeout=None):
        if url == API_URL:
            if json["messages"] == []:
                return MockResponse(200, {"choices": [{"message": {"content": "empty"}}]})
            elif json["messages"][0]["content"] == "error":
                return MockResponse(400, {})
            else:
                return MockResponse(200, {
                    "choices": [{"message": {"content": "response_content"}}],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5
                    }
                })
        raise Exception("Unexpected URL")
    
    monkeypatch.setattr(requests, "post", mock_post)

def test_happy_path(mock_requests_post):
    response = call_teacher(messages=[{"content": "test_message"}])
    assert response["success"] is True
    assert response["content"] == "response_content"
    assert response["input_tokens"] == 10
    assert response["output_tokens"] == 5

def test_empty_messages(mock_requests_post):
    response = call_teacher(messages=[])
    assert response["success"] is True
    assert response["content"] == "empty"

def test_error_case(mock_requests_post):
    response = call_teacher(messages=[{"content": "error"}])
    assert response["success"] is False
    assert response.get("error") is not None

def test_none_input():
    response = call_teacher(None)
    assert response["success"] is False
    assert response.get("error") is not None

def test_boundary_values(mock_requests_post):
    response = call_teacher(messages=[{"content": "test_message"}], max_tokens=1024)
    assert response["max_tokens"] == 1024