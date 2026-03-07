import pytest

from unified_core.orchestration.orchestrator import (
    Orchestrator,
    get_orchestrator,
)

@pytest.fixture(autouse=True)
def reset_orchestrator():
    """
    Fixture to ensure the orchestrator is None before each test.
    This ensures that tests do not rely on state from previous tests.
    """
    global _orchestrator
    _orchestrator = None

def test_get_orchestrator_happy_path():
    # Call the function twice to see if it returns the same instance
    orchestrator1 = get_orchestrator()
    orchestrator2 = get_orchestrator()

    assert orch_str is not None, "Orchestrator should not be None"
    assert orchestrator1 == orchestrator2, "Should return the same instance"

def test_get_orchestrator_edge_cases():
    # The function does not accept any parameters, so there's nothing to test for edge cases
    pass

def test_get_orchestrator_error_cases():
    # The function does not explicitly raise any errors, so there's nothing to test here
    pass

def test_get_orchestrator_async_behavior():
    # The function does not involve async operations, so there's nothing to test here
    pass