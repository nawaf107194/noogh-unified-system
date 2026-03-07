import pytest

def build_chat_context(user_query: str, history: list = None) -> list:
    """
    بناء سياق الدردشة.
    برومبت النظام أولاً، ثم التاريخ، ثم السؤال.
    """
    messages = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT}
    ]
    
    if history:
        for msg in history:
            if msg.get("role") != "system":
                messages.append(msg)
                
    messages.append({"role": "user", "content": user_query})
    
    return messages

# Test cases
def test_build_chat_context_happy_path():
    query = "Hello, how are you?"
    history = [
        {"role": "assistant", "content": "I'm good! How about yourself?"},
        {"role": "user", "content": "Fine"}
    ]
    expected = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "assistant", "content": "I'm good! How about yourself?"},
        {"role": "user", "content": "Fine"},
        {"role": "user", "content": query}
    ]
    assert build_chat_context(query, history) == expected

def test_build_chat_context_empty_history():
    query = "Hello, how are you?"
    expected = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    assert build_chat_context(query) == expected

def test_build_chat_context_none_history():
    query = "Hello, how are you?"
    expected = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    assert build_chat_context(query, None) == expected

def test_build_chat_context_invalid_history():
    query = "Hello, how are you?"
    history = [
        {"role": "system", "content": "Invalid prompt"},
        {"role": "user", "content": "Fine"}
    ]
    expected = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    assert build_chat_context(query, history) == expected

def test_build_chat_context_empty_query():
    query = ""
    history = [
        {"role": "assistant", "content": "I'm good! How about yourself?"},
        {"role": "user", "content": "Fine"}
    ]
    expected = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "assistant", "content": "I'm good! How about yourself?"},
        {"role": "user", "content": query}
    ]
    assert build_chat_context(query, history) == expected

def test_build_chat_context_none_query():
    query = None
    history = [
        {"role": "assistant", "content": "I'm good! How about yourself?"},
        {"role": "user", "content": "Fine"}
    ]
    expected = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "assistant", "content": "I'm good! How about yourself?"},
        {"role": "user", "content": query}
    ]
    assert build_chat_context(query, history) == expected