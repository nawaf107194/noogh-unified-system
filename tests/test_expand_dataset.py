import pytest

from expand_dataset import conv_slimorca, SYSTEM_PROMPT

@pytest.fixture
def sample_conversation():
    return [
        {"from": "system", "value": "System Prompt"},
        {"from": "human", "value": "User Input"},
        {"from": "gpt", "value": "Assistant Response"}
    ]

def test_happy_path(sample_conversation):
    result = conv_slimorca({"conversations": sample_conversation})
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 3

def test_empty_conversation():
    result = conv_slimorca({"conversations": []})
    assert result is None

def test_none_input():
    result = conv_slimorca(None)
    assert result is None

def test_single_conversation(sample_conversation):
    sample_conversation = sample_conversation[:1]
    result = conv_slimorca({"conversations": sample_conversation})
    assert result is None

def test_invalid_conversation_format():
    result = conv_slimorca({"conversations": "not a list"})
    assert result is None

def test_missing_required_keys(sample_conversation):
    for i in range(len(sample_conversation)):
        conv_copy = sample_conversation[:]
        del conv_copy[i]
        result = conv_slimorca({"conversations": [conv_copy]})
        assert result is None