import pytest

from unified_core.intelligence.multi_hypothesis_reasoning import MultiHypothesisReasoning

def test_init_happy_path():
    hypotheses = [
        {'name': 'bull', 'weight': 0.6},
        {'name': 'bear', 'weight': 0.4}
    ]
    mr = MultiHypothesisReasoning(hypotheses)
    assert mr.hypotheses == hypotheses
    assert mr.current_weights == {'bull': 0.6, 'bear': 0.4}

def test_init_empty_hypotheses():
    hypotheses = []
    mr = MultiHypothesisReasoning(hypotheses)
    assert mr.hypotheses == hypotheses
    assert mr.current_weights == {}

def test_init_none_hypotheses():
    hypotheses = None
    # Since the code does not explicitly raise an error for None, we check if it's handled gracefully
    mr = MultiHypothesisReasoning(hypotheses)
    assert mr.hypotheses == []
    assert mr.current_weights == {}

def test_init_invalid_hypotheses():
    hypotheses = [
        {'name': 'bull', 'weight': 0.6},
        {'name': None, 'weight': 0.4}  # Invalid name
    ]
    with pytest.raises(ValueError):
        MultiHypothesisReasoning(hypotheses)