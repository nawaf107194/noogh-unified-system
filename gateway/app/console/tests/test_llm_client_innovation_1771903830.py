import pytest

class MockLLMClient:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt

    def get_system_prompt(self) -> str:
        """Return the full UC3 Master Prompt for LLM calls."""
        return self.system_prompt

@pytest.fixture
def client_with_system_prompt():
    return MockLLMClient("Test System Prompt")

@pytest.fixture
def client_without_system_prompt():
    return MockLLMClient(None)

def test_get_system_prompt_happy_path(client_with_system_prompt):
    """Test happy path with normal inputs."""
    assert client_with_system_prompt.get_system_prompt() == "Test System Prompt"

def test_get_system_prompt_edge_case_none(client_without_system_prompt):
    """Test edge case where system prompt is None."""
    assert client_without_system_prompt.get_system_prompt() is None

def test_get_system_prompt_edge_case_empty_string(client_with_system_prompt):
    """Test edge case where system prompt is an empty string."""
    client = MockLLMClient("")
    assert client.get_system_prompt() == ""

def test_get_system_prompt_error_case_invalid_input():
    """Test error case with invalid input (should not happen as function does not accept any parameters)."""
    client = MockLLMClient("Test System Prompt")
    with pytest.raises(TypeError):
        client.get_system_prompt(123)

# Async behavior is not applicable in this synchronous function