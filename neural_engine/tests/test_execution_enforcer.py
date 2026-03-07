import pytest

from neural_engine.execution_enforcer import ExecutionEnforcer

class MockExecutionEnforcer(ExecutionEnforcer):
    def _is_execution(self, response: str) -> bool:
        return "execute" in response.lower()

    def _is_derivation(self, response: str) -> bool:
        return "derive" in response.lower()

    def _has_steps(self, response: str) -> bool:
        return "steps" in response.lower()

@pytest.fixture
def enforcer():
    return MockExecutionEnforcer()

def test_happy_path(enforcer):
    query = "What is the capital of France?"
    response = "The capital of France is Paris. To find it, execute 'locate Paris'. To derive its history, derive from historical records."
    assert enforcer.verify_and_enforce(query, response) == response

def test_edge_case_empty_response(enforcer):
    query = "What is the capital of France?"
    response = ""
    assert enforcer.verify_and_enforce(query, response) == "Cannot be concluded with certainty."

def test_edge_case_none_response(enforcer):
    query = "What is the capital of France?"
    response = None
    assert enforcer.verify_and_enforce(query, response) == "Cannot be concluded with certainty."

def test_error_case_invalid_execution(enforcer):
    query = "What is the capital of France?"
    response = "The capital of France is Paris. To find it, locate Paris."
    assert enforcer.verify_and_enforce(query, response) == "Cannot be concluded with certainty."

def test_error_case_invalid_derivation(enforcer):
    query = "What is the capital of France?"
    response = "To derive its history, derive from historical records."
    assert enforcer.verify_and_enforce(query, response) == "Cannot be concluded with certainty."

def test_error_case_no_steps(enforcer):
    query = "What is the capital of France?"
    response = "The capital of France is Paris. To find it, execute 'locate Paris'."
    assert enforcer.verify_and_enforce(query, response) == "Cannot be concluded with certainty."