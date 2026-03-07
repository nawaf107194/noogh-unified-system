import pytest
from unittest.mock import patch, MagicMock
from neural_engine.autonomic_system.policy_engine import PolicyEngine

@pytest.fixture
def policy_engine():
    engine = PolicyEngine()
    engine.blocked_actions = ["block"]
    engine.safe_actions = ["safe"]
    return engine

class TestShouldExecute:

    @patch('neural_engine.autonomic_system.policy_engine.logger')
    def test_happy_path(self, mock_logger, policy_engine):
        # Test safe action
        assert policy_engine.should_execute({"action": "safe"})
        mock_logger.debug.assert_called_once_with('✅ Policy approved (safe): safe')

        # Test auto-executable action with high confidence
        assert policy_engine.should_execute({"action": "auto", "auto_execute": True, "confidence": 0.9})
        mock_logger.info.assert_called_with('✅ Policy approved: auto (confidence=0.9)')

    @patch('neural_engine.autonomic_system.policy_engine.logger')
    def test_edge_cases(self, mock_logger, policy_engine):
        # Test empty proposal
        assert not policy_engine.should_execute({})
        mock_logger.warning.assert_not_called()

        # Test None action
        assert not policy_engine.should_execute({"action": None})
        mock_logger.warning.assert_not_called()

        # Test low confidence
        assert not policy_engine.should_execute({"action": "low_confidence", "auto_execute": True, "confidence": 0.75})
        mock_logger.warning.assert_called_with('⚠️  Low confidence (0.75): low_confidence')

    @patch('neural_engine.autonomic_system.policy_engine.logger')
    def test_error_cases(self, mock_logger, policy_engine):
        # Test invalid action type
        with pytest.raises(TypeError):
            policy_engine.should_execute(123)

        # Test invalid auto_execute type
        with pytest.raises(TypeError):
            policy_engine.should_execute({"action": "test", "auto_execute": "not_a_bool", "confidence": 0.9})

    @patch('neural_engine.autonomic_system.policy_engine.logger')
    def test_blocked_action(self, mock_logger, policy_engine):
        # Test blocked action
        assert not policy_engine.should_execute({"action": "block"})
        mock_logger.warning.assert_called_with('🔒 Policy blocked: block')

    @patch('neural_engine.autonomic_system.policy_engine.logger')
    def test_manual_approval_required(self, mock_logger, policy_engine):
        # Test action without auto_execute flag
        assert not policy_engine.should_execute({"action": "manual", "confidence": 0.9})
        mock_logger.info.assert_called_with('⏸️  Manual approval required: manual')