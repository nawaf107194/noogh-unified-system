import pytest

class MultiHypothesisReasoningMock:
    def __init__(self):
        self.current_weights = {
            "h1": 0.3,
            "h2": 0.4,
            "h3": 0.3
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

def test_update_hypothesis_weights_happy_path():
    reasoning = MultiHypothesisReasoningMock()
    reasoning.update_hypothesis_weights({"h1": 2.0, "h3": 3.0})
    
    expected_weights = {
        "h1": 0.3 * (1 + 2 / 5),
        "h2": 0.4,
        "h3": 0.3 * (1 + 3 / 5)
    }
    
    assert reasoning.current_weights == pytest.approx(expected_weights, rel=1e-9)

def test_update_hypothesis_weights_empty_evidence():
    reasoning = MultiHypothesisReasoningMock()
    reasoning.update_hypothesis_weights({})
    
    expected_weights = {
        "h1": 0.3 * 0.95,
        "h2": 0.4 * 0.95,
        "h3": 0.3 * 0.95
    }
    
    assert reasoning.current_weights == pytest.approx(expected_weights, rel=1e-9)

def test_update_hypothesis_weights_none_evidence():
    reasoning = MultiHypothesisReasoningMock()
    reasoning.update_hypothesis_weights(None)
    
    expected_weights = {
        "h1": 0.3 * 0.95,
        "h2": 0.4 * 0.95,
        "h3": 0.3 * 0.95
    }
    
    assert reasoning.current_weights == pytest.approx(expected_weights, rel=1e-9)

def test_update_hypothesis_weights_boundary_evidence():
    reasoning = MultiHypothesisReasoningMock()
    reasoning.update_hypothesis_weights({"h1": 1.0})
    
    expected_weights = {
        "h1": 0.3 * (1 + 1 / 1),
        "h2": 0.4,
        "h3": 0.3
    }
    
    assert reasoning.current_weights == pytest.approx(expected_weights, rel=1e-9)

def test_update_hypothesis_weights_invalid_evidence():
    reasoning = MultiHypothesisReasoningMock()
    with pytest.raises(TypeError):
        reasoning.update_hypothesis_weights("invalid_input")