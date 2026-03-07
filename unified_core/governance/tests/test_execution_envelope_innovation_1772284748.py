import pytest
from unittest.mock import patch, MagicMock
from unified_core.governance.execution_envelope import ExecutionEnvelope

class MockAuthContext:
    def __init__(self, user_id):
        self.user_id = user_id

def test_enter_happy_path():
    """Test the happy path where governance is enabled and all checks pass."""
    with patch('unified_core.governance.execution_envelope.time.time', return_value=1633024800.12345):
        with patch('unified_core.governance.execution_envelope.publish_event') as mock_publish:
            auth_context = MockAuthContext(user_id='user123')
            env = ExecutionEnvelope(auth_context=auth_context, component='test_component', params={})
            
            with env:
                pass

    assert env.start_time == 1633024800.12345
    mock_publish.assert_called_once_with(
        GovernanceEventType.EXECUTION_STARTED,
        component='test_component',
        user_id='user123',
        params={}
    )

def test_enter_governance_disabled():
    """Test the case where governance is disabled."""
    with patch('unified_core.governance.execution_envelope.ExecutionEnvelope._check_enabled', return_value=False):
        auth_context = MockAuthContext(user_id='user123')
        env = ExecutionEnvelope(auth_context=auth_context, component='test_component', params={})
        
        result = env.__enter__()
        
        assert result is env
        assert not hasattr(env, 'start_time')

def test_enter_auth_verification_failure():
    """Test the case where authentication verification fails."""
    with patch('unified_core.governance.execution_envelope.ExecutionEnvelope._check_enabled', return_value=True):
        with patch('unified_core.governance.execution_envelope.ExecutionEnvelope._verify_auth', side_effect=AuthenticationError):
            auth_context = MockAuthContext(user_id='user123')
            env = ExecutionEnvelope(auth_context=auth_context, component='test_component', params={})
            
            with pytest.raises(AuthenticationError):
                env.__enter__()

def test_enter_approval_check_failure():
    """Test the case where approval check fails."""
    with patch('unified_core.governance.execution_envelope.ExecutionEnvelope._check_enabled', return_value=True):
        with patch('unified_core.governance.execution_envelope.ExecutionEnvelope._verify_auth'):
            with patch('unified_core.governance.execution_envelope.ExecutionEnvelope._check_approval', side_effect=ApprovalError):
                auth_context = MockAuthContext(user_id='user123')
                env = ExecutionEnvelope(auth_context=auth_context, component='test_component', params={})
                
                with pytest.raises(ApprovalError):
                    env.__enter__()

class AuthenticationError(Exception):
    pass

class ApprovalError(Exception):
    pass