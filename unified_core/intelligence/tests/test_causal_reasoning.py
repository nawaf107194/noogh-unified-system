import pytest
from unified_core.intelligence.causal_reasoning import CausalReasoning
from unified_core.thinking.systems_thinking import SystemsThinking
from unified_core.filter.session_time_filter import SessionTimeFilter

@pytest.fixture
def systems_thinking():
    return SystemsThinking()

@pytest.fixture
def session_time_filter():
    return SessionTimeFilter()

def test_causal_reasoning_happy_path(systems_thinking, session_time_filter):
    causal_reasoning = CausalReasoning(systems_thinking, session_time_filter)
    assert causal_reasoning.systems_thinking is systems_thinking
    assert causal_reasoning.session_time_filter is session_time_filter

def test_causal_reasoning_none_inputs():
    with pytest.raises(TypeError):
        CausalReasoning(None, None)

def test_causal_reasoning_invalid_systems_thinking(systems_thinking, session_time_filter):
    with pytest.raises(TypeError):
        CausalReasoning("not_a_SystemsThinking", session_time_filter)

def test_causal_reasoning_invalid_session_time_filter(systems_thinking, session_time_filter):
    with pytest.raises(TypeError):
        CausalReasoning(systems_thinking, "not_a_SessionTimeFilter")