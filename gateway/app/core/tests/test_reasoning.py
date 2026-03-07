import pytest
from gateway.app.core.reasoning import ConfidenceScore

class MockReasoner:
    POSITIVE_MARKERS = {"good": 0.1, "excellent": 0.2}
    UNCERTAINTY_MARKERS = {"unsure": -0.1, "maybe": -0.05}
    OVERCONFIDENCE_MARKERS = {"certainly": -0.1, "definitely": -0.2}

@pytest.fixture
def reasoner():
    return MockReasoner()

def test_score_happy_path(reasoner):
    thought = "This is a good reasoning step"
    observation = "The observation confirms the reasoning."
    code_executed = True
    result = reasoner.score(thought, observation, code_executed)
    assert result.overall == 0.85
    assert result.reasoning_quality == 0.6
    assert result.evidence_strength == 0.2
    assert result.uncertainty_awareness == 0.4
    assert result.factors == {'positive_good': 0.1, 'has_observation': 0.15, 'no_error': 0.1, 'code_executed': 0.05}

def test_score_empty_thought(reasoner):
    thought = ""
    observation = "The observation confirms the reasoning."
    code_executed = True
    result = reasoner.score(thought, observation, code_executed)
    assert result.overall == 0.7
    assert result.reasoning_quality == 0.5
    assert result.evidence_strength == 0.2
    assert result.uncertainty_awareness == 0.5
    assert result.factors == {'has_observation': 0.15, 'no_error': 0.1, 'code_executed': 0.05}

def test_score_none_observation(reasoner):
    thought = "This is a good reasoning step"
    observation = None
    code_executed = False
    result = reasoner.score(thought, observation, code_executed)
    assert result.overall == 0.6
    assert result.reasoning_quality == 0.6
    assert result.evidence_strength == 0.0
    assert result.uncertainty_awareness == 0.5
    assert result.factors == {'positive_good': 0.1}

def test_score_overconfidence(reasoner):
    thought = "I am definitely certain about this reasoning step"
    observation = "The observation confirms the reasoning."
    code_executed = True
    result = reasoner.score(thought, observation, code_executed)
    assert result.overall == 0.75
    assert result.reasoning_quality == 0.4
    assert result.evidence_strength == 0.2
    assert result.uncertainty_awareness == 0.5
    assert result.factors == {'overconfidence_definitely': -0.2, 'has_observation': 0.15, 'no_error': 0.1, 'code_executed': 0.05}

def test_score_invalid_thought_type(reasoner):
    with pytest.raises(TypeError):
        reasoner.score(123, "observation", False)

def test_score_invalid_observation_type(reasoner):
    with pytest.raises(TypeError):
        reasoner.score("thought", 123, False)

def test_score_invalid_code_executed_type(reasoner):
    with pytest.raises(TypeError):
        reasoner.score("thought", "observation", "True")

# Since the function is synchronous, there's no need to test async behavior.