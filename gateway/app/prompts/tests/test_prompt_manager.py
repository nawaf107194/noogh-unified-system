import pytest
from unittest.mock import patch, MagicMock

# Assuming PromptManager is defined elsewhere and imported properly
from gateway.app.prompts.prompt_manager import PromptManager, get_prompt_manager

@pytest.fixture
def mock_prompt_manager():
    with patch('gateway.app.prompts.prompt_manager.PromptManager', autospec=True) as MockPromptManager:
        yield MockPromptManager

def test_get_prompt_manager_happy_path(mock_prompt_manager):
    # Test normal input
    storage_dir = "data/prompts"
    prompt_manager_instance = mock_prompt_manager.return_value
    result = get_prompt_manager(storage_dir)
    assert result == prompt_manager_instance
    mock_prompt_manager.assert_called_once_with(storage_dir)

def test_get_prompt_manager_empty_string(mock_prompt_manager):
    # Test empty string input
    storage_dir = ""
    prompt_manager_instance = mock_prompt_manager.return_value
    result = get_prompt_manager(storage_dir)
    assert result == prompt_manager_instance
    mock_prompt_manager.assert_called_once_with(storage_dir)

def test_get_prompt_manager_none_input(mock_prompt_manager):
    # Test None input
    storage_dir = None
    prompt_manager_instance = mock_prompt_manager.return_value
    result = get_prompt_manager(storage_dir)
    assert result == prompt_manager_instance
    mock_prompt_manager.assert_called_once_with("data/prompts")

def test_get_prompt_manager_invalid_input(mock_prompt_manager):
    # Test invalid input type
    storage_dir = 12345
    with pytest.raises(TypeError):
        get_prompt_manager(storage_dir)

def test_get_prompt_manager_singleton_behavior(mock_prompt_manager):
    # Test singleton behavior
    first_instance = get_prompt_manager()
    second_instance = get_prompt_manager("different/path")
    assert first_instance == second_instance
    mock_prompt_manager.assert_called_once()

# Assuming there's no async behavior in the given function
# If there were, we would use pytest-asyncio and mark the test as async
# For now, we skip the async behavior test case.