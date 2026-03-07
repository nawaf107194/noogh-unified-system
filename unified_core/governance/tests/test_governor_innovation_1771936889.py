import pytest

from unified_core.governance.governor import GovernanceDecision, decide, DecisionImpact, flags
from unittest.mock import patch

# Mocking dependencies
@patch('unified_core.governance.governor.flags.APPROVAL_GATE_ENABLED', True)
@patch('unified_core.governance.governor.classify')
def test_decide_happy_path(mock_classify):
    mock_classify.return_value = DecisionImpact.MEDIUM
    
    result = decide(component="test_component", user_id="user123")
    
    assert result == GovernanceDecision.ALLOW

@patch('unified_core.governance.governor.flags.APPROVAL_GATE_ENABLED', True)
@patch('unified_core.governance.governor.classify')
def test_decide_high_impact(mock_classify):
    mock_classify.return_value = DecisionImpact.HIGH
    
    result = decide(component="test_component", user_id="user123")
    
    assert result == GovernanceDecision.REQUIRE_APPROVAL

@patch('unified_core.governance.governor.flags.APPROVAL_GATE_ENABLED', True)
@patch('unified_core.governance.governor.classify')
def test_decide_critical_impact(mock_classify):
    mock_classify.return_value = DecisionImpact.CRITICAL
    
    result = decide(component="test_component", user_id="user123")
    
    assert result == GovernanceDecision.REQUIRE_APPROVAL

@patch('unified_core.governance.governor.flags.APPROVAL_GATE_ENABLED', True)
@patch('unified_core.governance.governor.classify')
def test_decide_unknown_impact(mock_classify):
    mock_classify.return_value = "UNKNOWN"
    
    with patch.object(decide, 'logger') as mock_logger:
        result = decide(component="test_component", user_id="user123")
        
        assert result == GovernanceDecision.BLOCK
        mock_logger.warning.assert_called_with(f"Unknown impact level: {mock_classify.return_value}")

@patch('unified_core.governance.governor.flags.APPROVAL_GATE_ENABLED', False)
def test_decide_approval_gate_disabled():
    result = decide(component="test_component", user_id="user123")
    
    assert result == GovernanceDecision.ALLOW

@patch('unified_core.governance.governor.classify')
def test_decide_none_params(mock_classify):
    mock_classify.return_value = DecisionImpact.MEDIUM
    
    result = decide(component="test_component", user_id="user123", params=None)
    
    assert result == GovernanceDecision.ALLOW

@patch('unified_core.governance.governor.classify')
def test_decide_empty_params(mock_classify):
    mock_classify.return_value = DecisionImpact.MEDIUM
    
    result = decide(component="test_component", user_id="user123", params={})
    
    assert result == GovernanceDecision.ALLOW