import pytest

SOVEREIGN_SYSTEM_PROMPT = "System prompt content"

@pytest.fixture
def setup_prompt():
    return SOVEREIGN_SYSTEM_PROMPT

def test_build_chat_context_happy_path(setup_prompt):
    user_query = "What is the weather today?"
    history = [{"role": "assistant", "content": "It's sunny outside."}]
    expected = [
        {"role": "system", "content": setup_prompt},
        {"role": "assistant", "content": "It's sunny outside."},
        {"role": "user", "content": "What is the weather today?"}
    ]
    assert build_chat_context(user_query, history) == expected

def test_build_chat_context_empty_history(setup_prompt):
    user_query = "What is the weather today?"
    history = []
    expected = [
        {"role": "system", "content": setup_prompt},
        {"role": "user", "content": "What is the weather today?"}
    ]
    assert build_chat_context(user_query, history) == expected

def test_build_chat_context_none_history(setup_prompt):
    user_query = "What is the weather today?"
    history = None
    expected = [
        {"role": "system", "content": setup_prompt},
        {"role": "user", "content": "What is the weather today?"}
    ]
    assert build_chat_context(user_query, history) == expected

def test_build_chat_context_with_system_message_in_history(setup_prompt):
    user_query = "What is the weather today?"
    history = [
        {"role": "system", "content": "Please answer with weather information only."},
        {"role": "assistant", "content": "It's sunny outside."}
    ]
    expected = [
        {"role": "system", "content": setup_prompt},
        {"role": "assistant", "content": "It's sunny outside."},
        {"role": "user", "content": "What is the weather today?"}
    ]
    assert build_chat_context(user_query, history) == expected

def test_build_chat_context_invalid_input_non_string_user_query(setup_prompt):
    user_query = 12345
    history = [{"role": "assistant", "content": "It's sunny outside."}]
    with pytest.raises(TypeError):
        build_chat_context(user_query, history)

def test_build_chat_context_invalid_input_non_list_history(setup_prompt):
    user_query = "What is the weather today?"
    history = "This is not a list"
    with pytest.raises(TypeError):
        build_chat_context(user_query, history)

def test_build_chat_context_async_behavior():
    # Since the function does not have any asynchronous behavior,
    # this test is just a placeholder to indicate that no async behavior exists.
    pass