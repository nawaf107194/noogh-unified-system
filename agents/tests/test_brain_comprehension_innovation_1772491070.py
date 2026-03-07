import pytest
from unittest.mock import patch, Mock
from your_module_name import _ask_brain  # Import the function to test

@pytest.fixture
def mock_urlopen():
    with patch('urllib.request.urlopen') as mock:
        yield mock

def test_happy_path(mock_urlopen):
    # Arrange
    prompt = "What is the capital of France?"
    expected_response = "Paris"
    
    mock_response = Mock()
    mock_response.read.return_value.decode.return_value = json.dumps({
        "choices": [{"message": {"content": expected_response}}]
    })
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # Act
    result = _ask_brain(prompt)
    
    # Assert
    assert result == expected_response

def test_empty_prompt(mock_urlopen):
    # Arrange
    prompt = ""
    expected_response = ""
    
    mock_response = Mock()
    mock_response.read.return_value.decode.return_value = json.dumps({
        "choices": [{"message": {"content": expected_response}}]
    })
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # Act
    result = _ask_brain(prompt)
    
    # Assert
    assert result == expected_response

def test_none_prompt(mock_urlopen):
    # Arrange
    prompt = None
    expected_response = ""
    
    mock_response = Mock()
    mock_response.read.return_value.decode.return_value = json.dumps({
        "choices": [{"message": {"content": expected_response}}]
    })
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # Act
    result = _ask_brain(prompt)
    
    # Assert
    assert result == expected_response

def test_boundary_max_tokens(mock_urlopen):
    # Arrange
    prompt = "What is the capital of France?"
    max_tokens = 1000
    expected_response = "Paris"
    
    mock_response = Mock()
    mock_response.read.return_value.decode.return_value = json.dumps({
        "choices": [{"message": {"content": expected_response}}]
    })
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # Act
    result = _ask_brain(prompt, max_tokens=max_tokens)
    
    # Assert
    assert result == expected_response

def test_invalid_input_type(mock_urlopen):
    # Arrange
    prompt = 123
    expected_response = ""
    
    mock_response = Mock()
    mock_response.read.return_value.decode.return_value = json.dumps({
        "choices": [{"message": {"content": expected_response}}]
    })
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # Act
    result = _ask_brain(prompt)
    
    # Assert
    assert result == expected_response

def test_network_error(mock_urlopen):
    # Arrange
    prompt = "What is the capital of France?"
    mock_urlopen.side_effect = URLError("Network error")
    
    # Act
    result = _ask_brain(prompt)
    
    # Assert
    assert result == ""