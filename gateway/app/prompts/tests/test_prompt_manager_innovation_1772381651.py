import pytest

from gateway.app.prompts.prompt_manager import PromptManager

@pytest.fixture
def prompt_manager():
    manager = PromptManager()
    # Initialize some prompts for testing
    manager.prompts = {
        "prompt1": "Template 1",
        "prompt2": "Template 2"
    }
    return manager

def test_activate_prompt_happy_path(prompt_manager):
    assert prompt_manager.activate_prompt("prompt1") is True
    assert prompt_manager.active_prompt_id == "prompt1"

def test_activate_prompt_edge_case_empty_string(prompt_manager):
    assert prompt_manager.activate_prompt("") is False
    assert prompt_manager.active_prompt_id is None

def test_activate_prompt_edge_case_none(prompt_manager):
    assert prompt_manager.activate_prompt(None) is False
    assert prompt_manager.active_prompt_id is None

def test_activate_prompt_error_case_invalid_input(prompt_manager):
    # This case will not raise an exception, so we just check the output
    assert prompt_manager.activate_prompt("prompt3") is False
    assert prompt_manager.active_prompt_id is None