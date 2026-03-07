import pytest
from unittest.mock import patch, Mock
from src.agents.self_healer import SelfHealer

# Assuming MODEL and VLLM_URL are defined somewhere in your project
MODEL = "test_model"
VLLM_URL = "http://localhost:8080"

@pytest.fixture
def self_healer():
    return SelfHealer()

@patch('urllib.request.urlopen')
def test_happy_path(mock_urlopen, self_healer):
    mock_response = Mock()
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "{\"code\": \"print(\\\"Hello, World!\\\")\"}"}}}]}'
    mock_urlopen.return_value = mock_response

    result = self_healer._ask_brain_for_code("Fix this code")
    
    assert result == {"code": "print(\"Hello, World!\")"}

@patch('urllib.request.urlopen')
def test_edge_case_empty_prompt(mock_urlopen, self_healer):
    mock_response = Mock()
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "{}"}}}]}'
    mock_urlopen.return_value = mock_response

    result = self_healer._ask_brain_for_code("")
    
    assert result == {}

@patch('urllib.request.urlopen')
def test_edge_case_none_prompt(mock_urlopen, self_healer):
    with pytest.raises(TypeError):
        self_healer._ask_brain_for_code(None)

@patch('urllib.request.urlopen')
def test_error_case_invalid_model(mock_urlopen, self_healer):
    mock_response = Mock()
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "{\"code\": \"print(\\\"Hello, World!\\\")\"}"}}}]}'
    mock_urlopen.return_value = mock_response

    with pytest.raises(ValueError) as e:
        self_healer._ask_brain_for_code("Fix this code", model="invalid_model")

    assert str(e.value) == "Invalid model: invalid_model"

@patch('urllib.request.urlopen')
def test_async_behavior(mock_urlopen, self_healer):
    mock_response = Mock()
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "{\"code\": \"print(\\\"Hello, World!\\\")\"}"}}}]}'
    mock_urlopen.return_value = mock_response

    result = self_healer._ask_brain_for_code("Fix this code")
    
    assert result == {"code": "print(\"Hello, World!\")"}