import pytest
from neural_engine.autonomic_system.policy_engine import PolicyEngine

@pytest.fixture
def policy_engine():
    return PolicyEngine()

def test_get_policy_summary_happy_path(policy_engine):
    # Test normal operation
    summary = policy_engine.get_policy_summary()
    
    # Verify the structure and content of the summary
    assert isinstance(summary, dict)
    assert "blocked_actions" in summary
    assert "safe_actions" in summary
    assert "confidence_threshold" in summary
    
    # Verify default confidence threshold
    assert summary["confidence_threshold"] == 0.8
    
def test_get_policy_summary_edge_cases(policy_engine):
    # Test empty actions
    summary = policy_engine.get_policy_summary()
    
    # Verify empty actions are properly initialized
    assert isinstance(summary["blocked_actions"], list)
    assert len(summary["blocked_actions"]) == 0
    
    assert isinstance(summary["safe_actions"], list)
    assert len(summary["safe_actions"]) == 0