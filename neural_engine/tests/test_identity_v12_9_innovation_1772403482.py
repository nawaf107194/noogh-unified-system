import pytest

from neural_engine.identity_v12_9 import build_chat_context, SOVEREIGN_SYSTEM_PROMPT

@pytest.fixture
def default_history():
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]

def test_build_chat_context_happy_path(default_history):
    user_query = "How are you?"
    expected_output = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": user_query}
    ]
    assert build_chat_context(user_query, default_history) == expected_output

def test_build_chat_context_empty_history():
    user_query = "How are you?"
    expected_output = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    assert build_chat_context(user_query, []) == expected_output

def test_build_chat_context_none_history():
    user_query = "How are you?"
    expected_output = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    assert build_chat_context(user_query, None) == expected_output

def test_build_chat_context_invalid_history():
    user_query = "How are you?"
    invalid_history = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "user", "content": "Hello"},
        {"role": "invalid_role", "content": "Hi"}
    ]
    expected_output = [
        {"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    assert build_chat_context(user_query, invalid_history) == expected_output