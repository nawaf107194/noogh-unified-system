import pytest
import numpy as np

class MultiHypothesisReasoningEnhancer:
    def __init__(self, num_hypotheses, initial_weights=None):
        self.num_hypotheses = num_hypotheses
        if initial_weights is None:
            self.hypothesis_weights = np.ones(num_hypotheses) / num_hypotheses
        else:
            self.hypothesis_weights = initial_weights

    def update_hypothesis_weights(self, outcomes):
        for i in range(self.num_hypotheses):
            if outcomes[i]:
                self.hypothesis_weights[i] *= 1.1
            else:
                self.hypothesis_weights[i] /= 1.1
        self.hypothesis_weights /= np.sum(self.hypothesis_weights)

# Happy path test
def test_update_hypothesis_weights_happy_path():
    enhancer = MultiHypothesisReasoningEnhancer(num_hypotheses=3)
    outcomes = [True, False, True]
    enhancer.update_hypothesis_weights(outcomes)
    expected_weights = np.array([1.21, 0.91, 1.21]) / 3.34
    np.testing.assert_almost_equal(enhancer.hypothesis_weights, expected_weights)

# Edge case: empty outcomes
def test_update_hypothesis_weights_empty_outcomes():
    enhancer = MultiHypothesisReasoningEnhancer(num_hypotheses=3)
    outcomes = []
    enhancer.update_hypothesis_weights(outcomes)
    assert np.allclose(enhancer.hypothesis_weights, 1 / 3)

# Edge case: None outcomes
def test_update_hypothesis_weights_none_outcomes():
    enhancer = MultiHypothesisReasoningEnhancer(num_hypotheses=3)
    outcomes = [None] * 3
    enhancer.update_hypothesis_weights(outcomes)
    assert np.allclose(enhancer.hypothesis_weights, 1 / 3)

# Error case: invalid outcome type (string instead of bool)
def test_update_hypothesis_weights_invalid_outcome_type():
    enhancer = MultiHypothesisReasoningEnhancer(num_hypotheses=3)
    outcomes = ['a', True, False]
    with pytest.raises(TypeError):
        enhancer.update_hypothesis_weights(outcomes)

# Error case: invalid outcome value (not a boolean)
def test_update_hypothesis_weights_invalid_outcome_value():
    enhancer = MultiHypothesisReasoningEnhancer(num_hypotheses=3)
    outcomes = [1, True, False]
    with pytest.raises(TypeError):
        enhancer.update_hypothesis_weights(outcomes)

# Error case: num_hypotheses does not match outcome length
def test_update_hypothesis_weights_mismatched_lengths():
    enhancer = MultiHypothesisReasoningEnhancer(num_hypotheses=3)
    outcomes = [True, False]
    with pytest.raises(ValueError):
        enhancer.update_hypothesis_weights(outcomes)

# Async behavior (not applicable in this case, as the function is synchronous)