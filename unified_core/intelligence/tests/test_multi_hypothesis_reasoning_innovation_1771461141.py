import pytest

from typing import List, Dict
from unittest.mock import patch

@pytest.fixture
def valid_hypotheses():
    return [
        {'name': 'bull', 'weight': 0.7},
        {'name': 'bear', 'weight': 0.3}
    ]

def test_init_happy_path(valid_hypotheses):
    from multi_hypothesis_reasoning import MultiHypothesisReasoning
    mhr = MultiHypothesisReasoning(valid_hypotheses)
    assert mhr.hypotheses == valid_hypotheses
    assert mhr.current_weights == {'bull': 0.7, 'bear': 0.3}

def test_init_empty_list():
    from multi_hypothesis_reasoning import MultiHypothesisReasoning
    mhr = MultiHypothesisReasoning([])
    assert mhr.hypotheses == []
    assert mhr.current_weights == {}

def test_init_none_input():
    from multi_hypothesis_reasoning import MultiHypothesisReasoning
    with pytest.raises(TypeError):
        MultiHypothesisReasoning(None)

def test_init_invalid_input_type():
    from multi_hypothesis_reasoning import MultiHypothesisReasoning
    with pytest.raises(TypeError):
        MultiHypothesisReasoning('not a list')

def test_init_missing_keys():
    from multi_hypothesis_reasoning import MultiHypothesisReasoning
    invalid_hypotheses = [{'name': 'bull'}, {'weight': 0.3}]
    with pytest.raises(KeyError):
        MultiHypothesisReasoning(invalid_hypotheses)

def test_init_with_boundaries():
    from multi_hypothesis_reasoning import MultiHypothesisReasoning
    boundary_hypotheses = [{'name': 'bull', 'weight': -1}, {'name': 'bear', 'weight': 2}]
    with pytest.raises(ValueError):
        MultiHypothesisReasoning(boundary_hypotheses)

def test_init_with_non_numeric_weight():
    from multi_hypothesis_reasoning import MultiHypothesisReasoning
    non_numeric_hypotheses = [{'name': 'bull', 'weight': 'high'}, {'name': 'bear', 'weight': 'low'}]
    with pytest.raises(ValueError):
        MultiHypothesisReasoning(non_numeric_hypotheses)

# Assuming no asynchronous behavior in the given init function
def test_init_async_behavior():
    from multi_hypothesis_reasoning import MultiHypothesisReasoning
    # Since there's no async behavior, this test will just pass if the sync version works
    valid_hypotheses = [{'name': 'bull', 'weight': 0.7}, {'name': 'bear', 'weight': 0.3}]
    mhr = MultiHypothesisReasoning(valid_hypotheses)
    assert mhr.hypotheses == valid_hypotheses
    assert mhr.current_weights == {'bull': 0.7, 'bear': 0.3}