import pytest
from unified_core.core.asaa import ASAA

class MockActionRequest:
    def __init__(self, source_beliefs=None):
        self.source_beliefs = source_beliefs

class MockBelief:
    def __init__(self, confidence):
        self.confidence = confidence

@pytest.fixture
def asaa_instance():
    return ASAA()

def test_happy_path(asaa_instance):
    # Arrange
    request = MockActionRequest(source_beliefs=[1, 2, 3])
    asaa_instance._beliefs = {
        1: MockBelief(0.8),
        2: MockBelief(0.4),
        3: MockBelief(0.6)
    }
    
    # Act
    fragility = asaa_instance._compute_fragility(request)
    
    # Assert
    assert fragility == 1.0 / 3

def test_edge_case_empty_request(asaa_instance):
    # Arrange
    request = MockActionRequest(source_beliefs=[])
    asaa_instance._beliefs = {}
    
    # Act
    fragility = asaa_instance._compute_fragility(request)
    
    # Assert
    assert fragility == 0.3

def test_edge_case_none_request(asaa_instance):
    # Arrange
    request = MockActionRequest(source_beliefs=None)
    asaa_instance._beliefs = {}
    
    # Act
    fragility = asaa_instance._compute_fragility(request)
    
    # Assert
    assert fragility == 0.3

def test_edge_case_no_involved_beliefs(asaa_instance):
    # Arrange
    request = MockActionRequest(source_beliefs=[1, 2])
    asaa_instance._beliefs = {
        1: MockBelief(0.7),
        2: MockBelief(0.3)
    }
    
    # Act
    fragility = asaa_instance._compute_fragility(request)
    
    # Assert
    assert fragility == 0.3

def test_error_case_invalid_belief_id(asaa_instance):
    # Arrange
    request = MockActionRequest(source_beliefs=[1, 2, 3])
    asaa_instance._beliefs = {}
    
    # Act & Assert
    with pytest.raises(KeyError):
        fragility = asaa_instance._compute_fragility(request)