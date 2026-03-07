import pytest
from typing import Dict, Any, Optional

def detect_agent_intent(user_message: str) -> Optional[Dict[str, Any]]:
    """
    Detect if user message requires agent capabilities
    
    Args:
        user_message: User's chat message
        
    Returns:
        dict with agent intent if detected, None otherwise
        Example: {"agent_type": "code_executor", "task": "run python script"}
    """
    if not isinstance(user_message, str):
        logging.error("Invalid input type. Expected string, got %s", type(user_message))
        raise TypeError("Expected a string input")

    message_lower = user_message.lower().strip()

    # Code execution patterns (English + Arabic)
    code_keywords = ["execute", "run code", "python", "script", "cmd", "نفذ", "شغّل", "شغل"]
    if any(kw in message_lower for kw in code_keywords):
        logging.info("Detected code execution intent: %s", user_message)
        return {
            "agent_type": "code_executor",
            "task": user_message,
            "capabilities": ["code_execution"]
        }

    # File operations patterns (English + Arabic)
    file_keywords = [
        "read file", "write file", "create file", "delete file",
        "اكتب ملف", "اقرأ ملف", "أنشئ ملف", "احذف ملف",
        "اقرا ملف", "انشئ ملف"
    ]
    if any(kw in message_lower for kw in file_keywords):
        logging.info("Detected file operation intent: %s", user_message)
        return {
            "agent_type": "file_manager",
            "task": user_message,
            "capabilities": ["file_operations"]
        }

    # No agent needed
    logging.info("No agent intent detected: %s", user_message)
    return None

# Happy path tests
def test_detect_agent_intent_code_execution():
    message = "Execute the python script"
    result = detect_agent_intent(message)
    assert result == {
        "agent_type": "code_executor",
        "task": "execute the python script",
        "capabilities": ["code_execution"]
    }

def test_detect_agent_intent_file_operations():
    message = "Create a new file"
    result = detect_agent_intent(message)
    assert result == {
        "agent_type": "file_manager",
        "task": "create a new file",
        "capabilities": ["file_operations"]
    }

# Edge case tests
def test_detect_agent_intent_empty_message():
    message = ""
    result = detect_agent_intent(message)
    assert result is None

def test_detect_agent_intent_none_input():
    result = detect_agent_intent(None)
    assert result is None

def test_detect_agent_intent_all_spaces():
    message = "   "
    result = detect_agent_intent(message)
    assert result is None

# Error case tests
def test_detect_agent_intent_invalid_input_type():
    with pytest.raises(TypeError):
        detect_agent_intent(123)

# Async behavior (if applicable - not required for this synchronous function)