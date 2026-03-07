import pytest
from neural_engine.attention_mechanism import AttentionMechanism

@pytest.fixture
def attention_mechanism():
    return AttentionMechanism(urgent_keywords=["urgent", "critical"])

def test_happy_path(attention_mechanism):
    input_data = {
        "content": "This is a normal message."
    }
    expected_output = {
        "content": "This is a normal message.",
        "attention_score": 0.5
    }
    assert attention_mechanism.weigh_importance(input_data) == expected_output

def test_edge_case_empty_content(attention_mechanism):
    input_data = {
        "content": ""
    }
    expected_output = {
        "content": ""
    }
    assert attention_mechanism.weigh_importance(input_data) == expected_output

def test_edge_case_none_content(attention_mechanism):
    input_data = None
    expected_output = None
    result = attention_mechanism.weigh_importance(input_data)
    assert result is None

def test_error_case_invalid_input_type(attention_mechanism):
    input_data = "not a dictionary"
    expected_output = None
    result = attention_mechanism.weigh_importance(input_data)
    assert result is None

def test_urgent_keywords_detected(attention_mechanism):
    input_data = {
        "content": "This message contains urgent keywords."
    }
    expected_output = {
        "content": "This message contains urgent keywords.",
        "attention_score": 0.9
    }
    assert attention_mechanism.weigh_importance(input_data) == expected_output

def test_urgent_keywords_not_detected(attention_mechanism):
    input_data = {
        "content": "This message does not contain urgent keywords."
    }
    expected_output = {
        "content": "This message does not contain urgent keywords.",
        "attention_score": 0.5
    }
    assert attention_mechanism.weigh_importance(input_data) == expected_output