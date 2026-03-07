import pytest

from unified_core.intelligence.multi_hypothesis_reasoning import MultiHypothesisReasoning

def test_init_happy_path():
    hypotheses = [
        {'name': 'bull', 'weight': 0.7},
        {'name': 'bear', 'weight': 0.3}
    ]
    mh_rea = MultiHypothesisReasoning(hypotheses)
    assert mh_rea.hypotheses == hypotheses
    assert mh_rea.current_weights == {'bull': 0.7, 'bear': 0.3}

def test_init_edge_case_empty_hypotheses():
    hypotheses = []
    mh_rea = MultiHypothesisReasoning(hypotheses)
    assert mh_rea.hypotheses == hypotheses
    assert mh_rea.current_weights == {}

def test_init_edge_case_none_hypotheses():
    hypotheses = None
    with pytest.raises(TypeError):
        MultiHypothesisReasoning(hypotheses)

def test_init_error_case_invalid_weight_type():
    hypotheses = [
        {'name': 'bull', 'weight': 0.7},
        {'name': 'bear', 'weight': 'invalid'}
    ]
    with pytest.raises(TypeError):
        MultiHypothesisReasoning(hypotheses)