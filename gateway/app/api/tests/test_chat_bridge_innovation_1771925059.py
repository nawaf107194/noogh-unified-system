import pytest

from gateway.app.api.chat_bridge import detect_agent_intent

def test_detect_agent_intent_happy_path():
    # Normal inputs with expected outcomes
    assert detect_agent_intent("Execute a python script") == {
        "agent_type": "code_executor",
        "task": "execute a python script",
        "capabilities": ["code_execution"]
    }
    assert detect_agent_intent("Read file example.txt") == {
        "agent_type": "file_manager",
        "task": "read file example.txt",
        "capabilities": ["file_operations"]
    }

def test_detect_agent_intent_edge_cases():
    # Empty string
    assert detect_agent_intent("") is None
    # None input
    assert detect_agent_intent(None) is None
    # Boundary cases (very long string)
    very_long_string = "execute" * 100 + " python script"
    assert detect_agent_intent(very_long_string) == {
        "agent_type": "code_executor",
        "task": very_long_string,
        "capabilities": ["code_execution"]
    }

def test_detect_agent_intent_error_cases():
    # Invalid input type
    with pytest.raises(TypeError) as e:
        detect_agent_intent(123)
    assert str(e.value) == "Expected a string input"