import pytest

from unified_core.governance.governor import Governor, GovernanceDecision, DecisionImpact, flags, logger, publish_event


@pytest.fixture
def governor():
    return Governor()


@pytest.mark.parametrize("component, user_id, params, expected_decision", [
    ("service_a", "user123", {"key": "value"}, GovernanceDecision.ALLOW),
    ("service_b", "user456", None, GovernanceDecision.ALLOW),
    ("service_c", "user789", {}, GovernanceDecision.ALLOW),
    ("critical_service", "user101", {"key": "value"}, GovernanceDecision.REQUIRE_APPROVAL),
    ("high_impact_service", "user202", {"key": "value"}, GovernanceDecision.REQUIRE_APPROVAL),
    ("unknown_service", "user303", {"key": "value"}, GovernanceDecision.BLOCK),
])
def test_decide(governor, component, user_id, params, expected_decision, monkeypatch):
    # Mock the flags.APPROVAL_GATE_ENABLED to True
    monkeypatch.setattr(flags, 'APPROVAL_GATE_ENABLED', True)
    
    # Mock the classify method to return a known impact level
    if "critical" in component:
        governor.classify = lambda _: DecisionImpact.CRITICAL
    elif "high" in component:
        governor.classify = lambda _: DecisionImpact.HIGH
    else:
        governor.classify = lambda _: DecisionImpact.LOW
    
    decision = governor.decide(component, user_id, params)
    
    assert decision == expected_decision


@pytest.mark.parametrize("component, user_id, params", [
    (None, "user123", {"key": "value"}),
    ("service_a", None, {"key": "value"}),
    ("service_a", "user123", None),
])
def test_decide_with_missing_inputs(governor, component, user_id, params):
    # Mock the flags.APPROVAL_GATE_ENABLED to True
    governor.flags = {'APPROVAL_GATE_ENABLED': True}
    
    decision = governor.decide(component, user_id, params)
    
    assert decision == GovernanceDecision.BLOCK


@pytest.mark.parametrize("component, user_id, params", [
    ("service_a", "user123", {"key": "value"}),
])
def test_decide_with_approval_gate_disabled(governor, component, user_id, params):
    # Mock the flags.APPROVAL_GATE_ENABLED to False
    governor.flags = {'APPROVAL_GATE_ENABLED': False}
    
    decision = governor.decide(component, user_id, params)
    
    assert decision == GovernanceDecision.ALLOW


@pytest.mark.parametrize("component, user_id, params", [
    ("unknown_service", "user123", {"key": "value"}),
])
def test_decide_with_unknown_impact(governor, component, user_id, params):
    # Mock the flags.APPROVAL_GATE_ENABLED to True
    governor.flags = {'APPROVAL_GATE_ENABLED': True}
    
    # Mock the classify method to return an unknown impact level
    governor.classify = lambda _: "UNKNOWN"
    
    decision = governor.decide(component, user_id, params)
    
    assert decision == GovernanceDecision.BLOCK