import pytest

class MultiHypothesisReasoning:
    def __init__(self):
        self.current_weights = {
            'h1': 0.5,
            'h2': 0.3,
            'h3': 0.2
        }

    def update_hypothesis_weights(self, evidence: Dict[str, float]):
        """
        Update the weights of each hypothesis based on new evidence.
        
        The evidence is provided as a dictionary where the key is the name of the hypothesis,
        and the value is the strength of the evidence supporting that hypothesis.
        
        :param evidence: Dictionary of evidence supporting each hypothesis.
        """
        total_evidence_strength = sum(evidence.values())
        normalized_evidence = {k: v / total_evidence_strength for k, v in evidence.items()}
        
        for hypothesis_name in self.current_weights.keys():
            if hypothesis_name in normalized_evidence:
                # Update the weight using a simple linear model
                self.current_weights[hypothesis_name] *= (1 + normalized_evidence[hypothesis_name])
            else:
                # If no evidence is provided for a hypothesis, slightly reduce its weight
                self.current_weights[hypothesis_name] *= 0.95

def update_hypothesis_weights(hypothesis_reasoning: MultiHypothesisReasoning, evidence: Dict[str, float]):
    return hypothesis_reasoning.update_hypothesis_weights(evidence)

# Tests
@pytest.fixture
def hypothesis_reasoning():
    return MultiHypothesisReasoning()

def test_update_hypothesis_weights_happy_path(hypothesis_reasoning):
    update_hypothesis_weights(hypothesis_reasoning, {'h1': 0.5})
    assert hypothesis_reasoning.current_weights['h1'] == pytest.approx(0.75)
    assert hypothesis_reasoning.current_weights['h2'] == pytest.approx(0.3)
    assert hypothesis_reasoning.current_weights['h3'] == pytest.approx(0.2)

def test_update_hypothesis_weights_empty_evidence(hypothesis_reasoning):
    update_hypothesis_weights(hypothesis_reasoning, {})
    assert all(weight == 0.95 * weight for weight in hypothesis_reasoning.current_weights.values())

def test_update_hypothesis_weights_none_evidence(hypothesis_reasoning):
    update_hypothesis_weights(hypothesis_reasoning, None)
    assert all(weight == 0.95 * weight for weight in hypothesis_reasoning.current_weights.values())

def test_update_hypothesis_weights_boundary_values(hypothesis_reasoning):
    update_hypothesis_weights(hypothesis_reasoning, {'h1': 1.0})
    assert hypothesis_reasoning.current_weights['h1'] == pytest.approx(2.5)

def test_update_hypothesis_weights_invalid_input_type(hypothesis_reasoning):
    with pytest.raises(TypeError):
        update_hypothesis_weights(hypothesis_reasoning, 'not a dict')