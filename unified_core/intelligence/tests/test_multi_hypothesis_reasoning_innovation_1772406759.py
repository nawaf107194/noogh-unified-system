import pytest

class MultiHypothesisReasoning:
    def __init__(self):
        self.current_weights = {'h1': 0.5, 'h2': 0.3, 'h3': 0.2}
    
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

@pytest.fixture
def multi_hypothesis_reasoning():
    return MultiHypothesisReasoning()

def test_update_hypothesis_weights_happy_path(multi_hypothesis_reasoning):
    evidence = {'h1': 2, 'h3': 1}
    multi_hypothesis_reasoning.update_hypothesis_weights(evidence)
    assert multi_hypothesis_reasoning.current_weights['h1'] == pytest.approx(0.75)
    assert multi_hypothesis_reasoning.current_weights['h3'] == pytest.approx(0.6)
    assert multi_hypothesis_reasoning.current_weights['h2'] == pytest.approx(0.29)

def test_update_hypothesis_weights_empty_evidence(multi_hypothesis_reasoning):
    evidence = {}
    multi_hypothesis_reasoning.update_hypothesis_weights(evidence)
    assert multi_hypothesis_reasoning.current_weights['h1'] == pytest.approx(0.475)
    assert multi_hypothesis_reasoning.current_weights['h2'] == pytest.approx(0.295)
    assert multi_hypothesis_reasoning.current_weights['h3'] == pytest.approx(0.23)

def test_update_hypothesis_weights_none_evidence(multi_hypothesis_reasoning):
    evidence = None
    multi_hypothesis_reasoning.update_hypothesis_weights(evidence)
    assert multi_hypothesis_reasoning.current_weights['h1'] == pytest.approx(0.475)
    assert multi_hypothesis_reasoning.current_weights['h2'] == pytest.approx(0.295)
    assert multi_hypothesis_reasoning.current_weights['h3'] == pytest.approx(0.23)

def test_update_hypothesis_weights_boundary_values(multi_hypothesis_reasoning):
    evidence = {'h1': 1, 'h2': 0, 'h3': 0}
    multi_hypothesis_reasoning.update_hypothesis_weights(evidence)
    assert multi_hypothesis_reasoning.current_weights['h1'] == pytest.approx(1.5)
    assert multi_hypothesis_reasoning.current_weights['h2'] == pytest.approx(0.95)
    assert multi_hypothesis_reasoning.current_weights['h3'] == pytest.approx(0.95)

def test_update_hypothesis_weights_invalid_input(multi_hypothesis_reasoning):
    evidence = {'h1': 'a', 'h2': 2}
    with pytest.raises(TypeError, match="unsupported operand type(s) for /: 'float' and 'str'"):
        multi_hypothesis_reasoning.update_hypothesis_weights(evidence)