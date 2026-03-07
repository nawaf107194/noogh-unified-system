import pytest

class HypothesisManager:
    def __init__(self):
        self.hypotheses = set()
        self.evidence = {}

    def add_hypothesis(self, hypothesis: str) -> None:
        if hypothesis not in self.hypotheses:
            self.hypotheses.add(hypothesis)
    
    def update_evidence(self, hypothesis: str, new_evidence: float) -> None:
        """
        Update the evidence for a given hypothesis.
        
        :param hypothesis: The hypothesis to update evidence for.
        :param new_evidence: New evidence value to add.
        """
        if hypothesis in self.hypotheses:
            self.evidence[hypothesis].append(new_evidence)
        else:
            raise ValueError(f"Hypothesis '{hypothesis}' not recognized.")

@pytest.fixture
def hypothesis_manager():
    return HypothesisManager()

def test_update_evidence_happy_path(hypothesis_manager):
    # Setup
    hypothesis_manager.add_hypothesis("H1")
    
    # Exercise
    hypothesis_manager.update_evidence("H1", 0.9)
    
    # Verify
    assert hypothesis_manager.evidence["H1"] == [0.9]

def test_update_evidence_empty_hypothesis(hypothesis_manager):
    # Exercise & Verify
    with pytest.raises(ValueError) as exc_info:
        hypothesis_manager.update_evidence("", 0.9)
    assert str(exc_info.value) == "Hypothesis '' not recognized."

def test_update_evidence_none_hypothesis(hypothesis_manager):
    # Exercise & Verify
    with pytest.raises(ValueError) as exc_info:
        hypothesis_manager.update_evidence(None, 0.9)
    assert str(exc_info.value) == "Hypothesis 'None' not recognized."

def test_update_evidence_boundary_value(hypothesis_manager):
    # Setup
    hypothesis_manager.add_hypothesis("H1")
    
    # Exercise
    hypothesis_manager.update_evidence("H1", 1.0)
    
    # Verify
    assert hypothesis_manager.evidence["H1"] == [1.0]

def test_update_evidence_negative_value(hypothesis_manager):
    # Setup
    hypothesis_manager.add_hypothesis("H1")
    
    # Exercise
    hypothesis_manager.update_evidence("H1", -0.5)
    
    # Verify
    assert hypothesis_manager.evidence["H1"] == [-0.5]

def test_update_evidence_non_numerical_value(hypothesis_manager):
    # Setup
    hypothesis_manager.add_hypothesis("H1")
    
    # Exercise & Verify
    with pytest.raises(ValueError) as exc_info:
        hypothesis_manager.update_evidence("H1", "not a float")
    assert str(exc_info.value) == "Hypothesis 'H1' not recognized."