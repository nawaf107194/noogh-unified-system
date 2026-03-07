import pytest

from unified_core.governance.execution_envelope import ExecutionEnvelope, GovernanceError

@pytest.fixture
def execution_envelope():
    return ExecutionEnvelope(component="test_component")

def test_happy_path_no_auth_gate_disabled(execution_envelope, flags):
    flags.AUTH_GATE_ENABLED = False
    result = execution_envelope._verify_auth()
    assert result is None

def test_happy_path_with_auth_gate_enabled(execution_envelope, flags):
    flags.AUTH_GATE_ENABLED = True
    execution_envelope.auth_context = {"user": "test_user"}
    result = execution_envelope._verify_auth()
    assert result is None

def test_edge_case_auth_context_none_dry_run(execution_envelope, flags):
    flags.AUTH_GATE_ENABLED = True
    flags.DRY_RUN = True
    result = execution_envelope._verify_auth()
    assert "Missing auth for" in result

def test_error_case_auth_context_none_no_dry_run(execution_envelope, flags):
    flags.AUTH_GATE_ENABLED = True
    flags.DRY_RUN = False
    with pytest.raises(GovernanceError) as exc_info:
        execution_envelope._verify_auth()
    assert "Auth required for" in str(exc_info.value)