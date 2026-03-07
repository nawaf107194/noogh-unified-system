import pytest
from unified_core.intelligence.active_questioning import ActiveQuestioning
from unittest.mock import patch, Mock

# Mock the NeuralEngineClient and its methods
class MockNeuralEngineClient:
    def call(self, prompt):
        return "Mocked response"

@patch('unified_core.intelligence.active_questioning.NeuralEngineClient', new=MockNeuralEngineClient)
@patch('logging.info')
def test_answer_why_happy_path(mock_info):
    # Arrange
    active_questioning = ActiveQuestioning()
    current = "The sun is shining."
    question = "Why is the sky blue?"
    
    # Act
    result = active_questioning._answer_why(current, question)
    
    # Assert
    assert result == "Mocked response"
    mock_info.assert_called_once_with("Asking NeuralEngine (Why): Why is the sky blue?")
    assert len(mock_info.call_args_list) == 1

@patch('unified_core.intelligence.active_questioning.NeuralEngineClient', new=MockNeuralEngineClient)
@patch('logging.info')
def test_answer_why_empty_input(mock_info):
    # Arrange
    active_questioning = ActiveQuestioning()
    current = ""
    question = "Why is the sky blue?"
    
    # Act
    result = active_questioning._answer_why(current, question)
    
    # Assert
    assert result == "Mocked response"
    mock_info.assert_called_once_with("Asking NeuralEngine (Why): Why is the sky blue?")
    assert len(mock_info.call_args_list) == 1

@patch('unified_core.intelligence.active_questioning.NeuralEngineClient', new=MockNeuralEngineClient)
@patch('logging.info')
def test_answer_why_none_input(mock_info):
    # Arrange
    active_questioning = ActiveQuestioning()
    current = None
    question = "Why is the sky blue?"
    
    # Act
    result = active_questioning._answer_why(current, question)
    
    # Assert
    assert result == "Mocked response"
    mock_info.assert_called_once_with("Asking NeuralEngine (Why): Why is the sky blue?")
    assert len(mock_info.call_args_list) == 1

@patch('unified_core.intelligence.active_questioning.NeuralEngineClient', new=MockNeuralEngineClient)
@patch('logging.info')
def test_answer_why_boundary_case(mock_info):
    # Arrange
    active_questioning = ActiveQuestioning()
    current = "The sun is shining."
    question = "Why is the sky blue?"
    
    # Act
    result = active_questioning._answer_why(current, question)
    
    # Assert
    assert result == "Mocked response"
    mock_info.assert_called_once_with("Asking NeuralEngine (Why): Why is the sky blue?")
    assert len(mock_info.call_args_list) == 1

@patch('unified_core.intelligence.active_questioning.NeuralEngineClient', new=MockNeuralEngineClient)
@patch('logging.info')
def test_answer_why_invalid_input(mock_info):
    # Arrange
    active_questioning = ActiveQuestioning()
    current = "The sun is shining."
    question = 123
    
    # Act & Assert
    with pytest.raises(AssertionError) as excinfo:
        result = active_questioning._answer_why(current, question)
    
    assert str(excinfo.value) == "Assertion failed: 'question' must be a string"

@patch('unified_core.intelligence.active_questioning.NeuralEngineClient', new=MockNeuralEngineClient)
@patch('logging.info')
def test_answer_why_with_async_behavior(mock_info):
    # Arrange
    active_questioning = ActiveQuestioning()
    current = "The sun is shining."
    question = "Why is the sky blue?"
    
    # Mock NeuralEngineClient to be async
    class AsyncMockNeuralEngineClient:
        async def call(self, prompt):
            return "Async mocked response"
    
    with patch('unified_core.intelligence.active_questioning.NeuralEngineClient', new=AsyncMockNeuralEngineClient) as mock_client:
        # Act
        result = active_questioning._answer_why(current, question)
        
        # Assert
        assert result == "Async mocked response"
        mock_info.assert_called_once_with("Asking NeuralEngine (Why): Why is the sky blue?")
        assert len(mock_info.call_args_list) == 1