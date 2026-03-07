import pytest

class ExecutionEnforcer:
    def _reinterprets_role(self, response: str) -> bool:
        """Detect role reinterpretation"""
        role_reinterpretation = [
            "this is a test",
            "performance evaluation",
            "not an assistance question",
            "هذا اختبار",
            "تقييم",
        ]
        return any(phrase in response.lower() for phrase in role_reinterpretation)

@pytest.fixture
def execution_enforcer():
    return ExecutionEnforcer()

def test_happy_path(execution_enforcer):
    assert execution_enforcer._reinterprets_role("This is a test") == True
    assert execution_enforcer._reinterprets_role("Performance Evaluation") == True
    assert execution_enforcer._reinterprets_role("Not an assistance question") == True
    assert execution_enforcer._reinterprets_role("هذا اختبار") == True
    assert execution_enforcer._reinterprets_role("تقييم") == True

def test_edge_cases(execution_enforcer):
    assert execution_enforcer._reinterprets_role("") == False
    assert execution_enforcer._reinterprets_role(None) == False
    assert execution_enforcer._reinterprets_role("This is a test, but not exactly") == True
    assert execution_enforcer._reinterprets_role("Not in the list at all") == False

def test_error_cases(execution_enforcer):
    with pytest.raises(TypeError):
        execution_enforcer._reinterprets_role(123)