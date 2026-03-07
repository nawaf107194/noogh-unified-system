import pytest
from typing import List, Dict

# Assuming the module is imported correctly
from unified_core.intelligence.multi_hypothesis_reasoning import MultiHypothesisReasoning

class TestMultiHypothesisReasoningInit:

    @pytest.fixture
    def setup_hypotheses(self):
        return [
            {'name': 'bull', 'weight': 0.7},
            {'name': 'bear', 'weight': 0.3}
        ]

    def test_happy_path(self, setup_hypotheses):
        mhr = MultiHypothesisReasoning(setup_hypotheses)
        assert mhr.hypotheses == setup_hypotheses
        assert mhr.current_weights == {'bull': 0.7, 'bear': 0.3}

    def test_empty_list(self):
        with pytest.raises(ValueError, match="hypotheses must not be empty"):
            MultiHypothesisReasoning([])

    def test_none_input(self):
        with pytest.raises(TypeError, match="hypotheses must be a list"):
            MultiHypothesisReasoning(None)

    def test_invalid_hypothesis_format(self):
        invalid_hypotheses = [{'name': 'bull'}, {'weight': 0.3}]
        with pytest.raises(KeyError, match="'name' or 'weight' missing in hypothesis"):
            MultiHypothesisReasoning(invalid_hypotheses)

    def test_non_dict_in_list(self):
        invalid_hypotheses = ['bull', 'bear']
        with pytest.raises(TypeError, match="Each hypothesis must be a dictionary"):
            MultiHypothesisReasoning(invalid_hypotheses)

    def test_boundary_values(self):
        boundary_hypotheses = [{'name': 'bull', 'weight': -0.1}, {'name': 'bear', 'weight': 1.1}]
        with pytest.raises(ValueError, match="Weights must be between 0 and 1"):
            MultiHypothesisReasoning(boundary_hypotheses)

    def test_async_behavior(self):
        # Since the __init__ method does not involve any asynchronous operations,
        # there's no need to test for async behavior. This test is just a placeholder
        # to show that we've considered it.
        pass