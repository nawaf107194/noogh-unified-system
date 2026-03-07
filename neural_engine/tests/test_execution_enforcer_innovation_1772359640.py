import pytest

class TestValidationExecution:

    def test_happy_path(self):
        execution_enforcer = ExecutionEnforcer()
        result = execution_enforcer.validate_execution("Step 1: Start", "this is a test")
        assert result == {"valid": False, "reason": "CONVERSATIONAL_EVASION", "action": "REJECT_AND_ENFORCE_N/A"}

    def test_edge_case_empty_query(self):
        execution_enforcer = ExecutionEnforcer()
        result = execution_enforcer.validate_execution("", "this is a test")
        assert result == {"valid": False, "reason": "NO_EXECUTION_DETECTED", "action": "FORCE_FAILURE_GATE"}

    def test_edge_case_none_query(self):
        execution_enforcer = ExecutionEnforcer()
        result = execution_enforcer.validate_execution(None, "this is a test")
        assert result == {"valid": False, "reason": "NO_EXECUTION_DETECTED", "action": "FORCE_FAILURE_GATE"}

    def test_error_case_invalid_input_type_query(self):
        execution_enforcer = ExecutionEnforcer()
        with pytest.raises(TypeError):
            execution_enforcer.validate_execution(12345, "this is a test")

    def test_error_case_invalid_input_type_response(self):
        execution_enforcer = ExecutionEnforcer()
        result = execution_enforcer.validate_execution("Step 1: Start", 12345)
        assert result == {"valid": False, "reason": "NO_EXECUTION_DETECTED", "action": "FORCE_FAILURE_GATE"}