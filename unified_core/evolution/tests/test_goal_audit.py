import pytest

from unified_core.evolution.goal_audit import get_goal_audit_engine, GoalAuditEngine

@pytest.fixture(scope="module")
def audit_engine_instance():
    return GoalAuditEngine()

def test_get_goal_audit_engine_happy_path(audit_engine_instance):
    """Test the happy path where the engine instance is not yet created."""
    global _audit_engine_instance
    _audit_engine_instance = None
    result = get_goal_audit_engine()
    assert isinstance(result, GoalAuditEngine)
    assert result == audit_engine_instance

def test_get_goal_audit_engine_cached_instance(audit_engine_instance):
    """Test the case where the engine instance is already created."""
    global _audit_engine_instance
    _audit_engine_instance = audit_engine_instance
    result = get_goal_audit_engine()
    assert isinstance(result, GoalAuditEngine)
    assert result == audit_engine_instance

def test_get_goal_audit_engine_no_global_var():
    """Test the case where there is no global variable for the engine instance."""
    global _audit_engine_instance
    del _audit_engine_instance  # Ensure the global var does not exist
    result = get_goal_audit_engine()
    assert isinstance(result, GoalAuditEngine)