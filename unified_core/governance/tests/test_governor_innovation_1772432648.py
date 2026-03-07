import pytest

from unified_core.governance.governor import Governor, GovernanceDecision, DecisionImpact
from unified_core.flags import APPROVAL_GATE_ENABLED
from unified_core.events import publish_event
from unittest.mock import patch, MagicMock

class TestGovernor:
    def test_happy_path_approve_low_impact(self):
        gov = Governor()
        with patch.object(gov, 'classify', return_value=DecisionImpact.LOW):
            decision = gov.decide('component123', 'user456')
            assert decision == GovernanceDecision.ALLOW

    def test_happy_path_require_approval_high_impact(self):
        gov = Governor()
        with patch.object(gov, 'classify', return_value=DecisionImpact.HIGH):
            publish_event_mock = MagicMock()
            with patch('unified_core.events.publish_event', new=publish_event_mock):
                decision = gov.decide('component123', 'user456')
                assert decision == GovernanceDecision.REQUIRE_APPROVAL
                publish_event_mock.assert_called_once_with(
                    GovernanceEventType.APPROVAL_REQUESTED,
                    component='component123',
                    user_id='user456',
                    impact=DecisionImpact.HIGH.value,
                    params=None
                )

    def test_edge_case_empty_component(self):
        gov = Governor()
        decision = gov.decide('', 'user456')
        assert decision == GovernanceDecision.BLOCK

    def test_edge_case_none_user_id(self):
        gov = Governor()
        decision = gov.decide('component123', None)
        assert decision == GovernanceDecision.BLOCK

    def test_edge_case_boundary_low_impact(self):
        gov = Governor()
        with patch.object(gov, 'classify', return_value=DecisionImpact.MEDIUM):
            decision = gov.decide('component123', 'user456')
            assert decision == GovernanceDecision.ALLOW

    def test_edge_case_boundary_high_impact(self):
        gov = Governor()
        with patch.object(gov, 'classify', return_value=DecisionImpact.CRITICAL):
            publish_event_mock = MagicMock()
            with patch('unified_core.events.publish_event', new=publish_event_mock):
                decision = gov.decide('component123', 'user456')
                assert decision == GovernanceDecision.REQUIRE_APPROVAL
                publish_event_mock.assert_called_once_with(
                    GovernanceEventType.APPROVAL_REQUESTED,
                    component='component123',
                    user_id='user456',
                    impact=DecisionImpact.CRITICAL.value,
                    params=None
                )

    def test_error_case_disabled_approval_gate(self):
        gov = Governor()
        with patch.object(APPROVAL_GATE_ENABLED, 'value', False):
            decision = gov.decide('component123', 'user456')
            assert decision == GovernanceDecision.ALLOW

    def test_error_case_unknown_impact(self):
        gov = Governor()
        with patch.object(gov, 'classify', return_value='UNKNOWN'):
            decision = gov.decide('component123', 'user456')
            assert decision == GovernanceDecision.BLOCK