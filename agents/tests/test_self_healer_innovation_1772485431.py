import pytest
from unittest.mock import patch, MagicMock
from agents.self_healer import SelfHealer

# Mock the necessary functions and variables
MODEL = "test_model"
VLLM_URL = "http://test.url"
logger = MagicMock()

@pytest.fixture
def self_healer():
    return SelfHealer()

@patch('urllib.request.urlopen')
def test_happy_path(mock_open):
    # Prepare mock response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "{ \"code\": \"print(\'Hello, World!\')\" }"}}]}'
    
    # Configure mock
    mock_open.return_value.__enter__.return_value = mock_response
    
    sh = SelfHealer()
    result = sh._ask_brain_for_code("Fix this code")
    
    assert result == {"code": "print('Hello, World!')"}

@patch('urllib.request.urlopen')
def test_edge_case_empty_prompt(mock_open):
    # Configure mock
    mock_open.return_value.__enter__.return_value.read.return_value = b'{"choices": [{"message": {"content": ""}}]}'
    
    sh = SelfHealer()
    result = sh._ask_brain_for_code("")
    
    assert result == {}

@patch('urllib.request.urlopen')
def test_edge_case_none_prompt(mock_open):
    # Configure mock
    mock_open.return_value.__enter__.return_value.read.return_value = b'{"choices": [{"message": {"content": None}}]}'
    
    sh = SelfHealer()
    result = sh._ask_brain_for_code(None)
    
    assert result == {}

@patch('urllib.request.urlopen')
def test_error_case_invalid_json(mock_open):
    # Prepare mock response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "Not a valid JSON"}}]}'
    
    # Configure mock
    mock_open.return_value.__enter__.return_value = mock_response
    
    sh = SelfHealer()
    result = sh._ask_brain_for_code("Fix this code")
    
    assert result == {}

@patch('urllib.request.urlopen')
def test_error_case_no_json_content(mock_open):
    # Prepare mock response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"choices": [{"message": {"content": "Some text without JSON"}}]}'
    
    # Configure mock
    mock_open.return_value.__enter__.return_value = mock_response
    
    sh = SelfHealer()
    result = sh._ask_brain_for_code("Fix this code")
    
    assert result == {}

@patch('urllib.request.urlopen')
def test_error_case_exception(mock_open):
    # Configure mock to raise an exception
    mock_open.side_effect = Exception("Test exception")
    
    sh = SelfHealer()
    result = sh._ask_brain_for_code("Fix this code")
    
    assert result == {}