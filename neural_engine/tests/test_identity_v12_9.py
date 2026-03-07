import pytest

SOVEREIGN_SYSTEM_PROMPT = "System prompt content"

@pytest.fixture
def setup_prompt():
    return SOVEREIGN_SYSTEM_PROMPT

@pytest.mark.parametrize("user_query,history,expected", [
    ("Hello, how are you?", [{"role": "assistant", "content": "I'm good, thanks!"}], [{"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT}, {"role": "assistant", "content": "I'm good, thanks!"}, {"role": "user", "content": "Hello, how are you?"}]),
    ("What's the weather like?", [], [{"role": "system", "content": SOVEREIGN_SYSTEM_PROMPT}, {"role": "user", "content": "What's the weather like?"}])
])
def test_build_chat_context_happy_path(user_query, history, expected):
    from neural_engine.identity_v12_9 import build_chat_context
    result = build_chat_context(user_query, history)
    assert result == expected

@pytest.mark.parametrize("user_query,history", [
    ("", None),
    ("", []),
    ("", [{}]),
    ("", [{"role": "system", "content": "Some content"}]),
    ("", [{"role": "assistant", "content": "Some content"}, {"role": "system", "content": "Some content"}])
])
def test_build_chat_context_edge_cases(user_query, history):
    from neural_engine.identity_v12_9 import build_chat_context
    result = build_chat_context(user_query, history)
    assert len(result) > 0
    assert result[0]["role"] == "system"
    assert result[-1]["role"] == "user"
    assert result[-1]["content"] == user_query

@pytest.mark.parametrize("user_query,history", [
    (None, None),
    (123, []),
    ([], [{}]),
    ({"role": "user", "content": "Invalid query"}, [{"role": "assistant", "content": "Some content"}])
])
def test_build_chat_context_error_cases(user_query, history):
    from neural_engine.identity_v12_9 import build_chat_context
    with pytest.raises(TypeError):
        build_chat_context(user_query, history)

# Since the function does not have any asynchronous behavior, no async tests are needed.