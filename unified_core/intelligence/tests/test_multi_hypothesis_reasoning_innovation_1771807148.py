import pytest

class MockMultiHypothesisReasoning:
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

def test_update_hypothesis_weights_happy_path():
    obj = MockMultiHypothesisReasoning()
    evidence = {'h1': 0.2, 'h3': 0.8}
    expected_weights = {
        'h1': 0.5 * (1 + 0.2),
        'h2': 0.3 * 0.95,
        'h3': 0.2 * (1 + 0.8)
    }
    obj.update_hypothesis_weights(evidence)
    assert obj.current_weights == expected_weights

def test_update_hypothesis_weights_empty_evidence():
    obj = MockMultiHypothesisReasoning()
    evidence = {}
    for hypothesis_name in obj.current_weights.keys():
        assert obj.current_weights[hypothesis_name] == obj.current_weights[hypothesis_name] * 0.95

def test_update_hypothesis_weights_none_evidence():
    obj = MockMultiHypothesisReasoning()
    evidence = None
    obj.update_hypothesis_weights(evidence)
    for hypothesis_name in obj.current_weights.keys():
        assert obj.current_weights[hypothesis_name] == obj.current_weights[hypothesis_name] * 0.95

def test_update_hypothesis_weights_invalid_evidence_type():
    obj = MockMultiHypothesisReasoning()
    evidence = "not a dictionary"
    expected_result = False
    result = obj.update_hypothesis_weights(evidence)
    assert result == expected_result