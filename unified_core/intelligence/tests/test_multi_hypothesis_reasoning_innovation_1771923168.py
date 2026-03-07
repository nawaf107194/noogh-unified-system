import pytest
from typing import List, Dict

class MultiHypothesisReasoning:
    def __init__(self, hypotheses: List[Dict[str, float]]):
        """
        Initialize the multi-hypothesis reasoning module with a list of hypotheses.
        
        Each hypothesis is represented as a dictionary with keys 'name' and 'weight'.
        The 'name' key corresponds to the name of the hypothesis (e.g., 'bull', 'bear').
        The 'weight' key corresponds to the initial confidence weight assigned to the hypothesis.
        
        :param hypotheses: List of hypotheses with their initial weights.
        """
        self.hypotheses = hypotheses
        self.current_weights = {h['name']: h['weight'] for h in hypotheses}

# Happy path test
def test_init_happy_path():
    hypotheses = [{'name': 'bull', 'weight': 0.7}, {'name': 'bear', 'weight': 0.3}]
    reasoning_module = MultiHypothesisReasoning(hypotheses)
    assert reasoning_module.hypotheses == hypotheses
    assert reasoning_module.current_weights == {'bull': 0.7, 'bear': 0.3}

# Edge case: empty list
def test_init_empty_hypotheses():
    hypotheses = []
    reasoning_module = MultiHypothesisReasoning(hypotheses)
    assert reasoning_module.hypotheses == []
    assert reasoning_module.current_weights == {}

# Edge case: None input
def test_init_none_input():
    with pytest.raises(TypeError):
        MultiHypothesisReasoning(None)

# Error case: invalid hypothesis format (missing 'weight')
def test_init_invalid_hypothesis_format_missing_weight():
    hypotheses = [{'name': 'bull'}, {'name': 'bear', 'weight': 0.3}]
    reasoning_module = MultiHypothesisReasoning(hypotheses)
    assert reasoning_module.hypotheses == [{'name': 'bull'}]
    assert reasoning_module.current_weights == {'bull': None}

# Error case: invalid hypothesis format (non-numeric weight)
def test_init_invalid_hypothesis_format_non_numeric_weight():
    hypotheses = [{'name': 'bull', 'weight': 'a'}, {'name': 'bear', 'weight': 0.3}]
    reasoning_module = MultiHypothesisReasoning(hypotheses)
    assert reasoning_module.hypotheses == [{'name': 'bull', 'weight': 'a'}]
    assert reasoning_module.current_weights == {'bull': None}

# Error case: invalid hypothesis format (negative weight)
def test_init_invalid_hypothesis_format_negative_weight():
    hypotheses = [{'name': 'bull', 'weight': -0.3}, {'name': 'bear', 'weight': 0.7}]
    reasoning_module = MultiHypothesisReasoning(hypotheses)
    assert reasoning_module.hypotheses == [{'name': 'bull', 'weight': -0.3}]
    assert reasoning_module.current_weights == {'bull': None}