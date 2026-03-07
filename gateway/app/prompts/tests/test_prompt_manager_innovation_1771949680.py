import pytest
from unittest.mock import patch, MagicMock
from gateway.app.prompts.prompt_manager import PromptManager, PromptTemplate
import os
import json

@pytest.fixture
def prompt_manager():
    return PromptManager(storage_dir="test_storage")

def test_load_prompts_happy_path(prompt_manager):
    # Arrange
    prompts_file = "test_storage/prompts.json"
    data = [
        {"id": "1", "template": "Hello, {name}!"},
        {"id": "2", "template": "Goodbye, {name}!"}
    ]
    with open(prompts_file, "w") as f:
        json.dump(data, f)

    # Act
    prompt_manager._load_prompts()

    # Assert
    assert len(prompt_manager.prompts) == 2
    assert "1" in prompt_manager.prompts
    assert "2" in prompt_manager.prompts

def test_load_prompts_empty_file(prompt_manager):
    # Arrange
    prompts_file = "test_storage/prompts.json"
    with open(prompts_file, "w") as f:
        json.dump([], f)

    # Act
    prompt_manager._load_prompts()

    # Assert
    assert len(prompt_manager.prompts) == 0

def test_load_prompts_non_existent_file(prompt_manager):
    # Arrange
    prompts_file = "non_existent_storage/prompts.json"

    # Act
    with patch.object(os, 'path', **{"exists.return_value": False}):
        prompt_manager._load_prompts()

    # Assert
    assert len(prompt_manager.prompts) == 0

def test_load_prompts_invalid_data(prompt_manager):
    # Arrange
    prompts_file = "test_storage/prompts.json"
    data = [
        {"id": "1", "template": "Hello, {name}!"},
        {"invalid_key": "value"}
    ]
    with open(prompts_file, "w") as f:
        json.dump(data, f)

    # Act
    prompt_manager._load_prompts()

    # Assert
    assert len(prompt_manager.prompts) == 1
    assert "1" in prompt_manager.prompts

def test_load_prompts_with_async_behavior(prompt_manager):
    # Arrange
    prompts_file = "test_storage/prompts.json"
    data = [
        {"id": "1", "template": "Hello, {name}!"},
        {"id": "2", "template": "Goodbye, {name}!"}
    ]
    with open(prompts_file, "w") as f:
        json.dump(data, f)

    # Mock the PromptTemplate constructor
    with patch.object(PromptManager, 'prompts', new_callable=dict) as mock_prompts:
        # Act
        prompt_manager._load_prompts()

        # Assert
        assert len(mock_prompts) == 2
        assert "1" in mock_prompts
        assert "2" in mock_prompts

# Clean up after tests
def teardown_module():
    import shutil
    shutil.rmtree("test_storage")
    shutil.rmtree("non_existent_storage")