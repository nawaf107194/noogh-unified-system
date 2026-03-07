import pytest
from unittest.mock import MagicMock
from typing import Any

# Assuming the Orchestrator class and _orchestrator variable are defined elsewhere
# For the sake of this example, we'll mock them out.
Orchestrator = MagicMock()
_orchestrator = None

def get_orchestrator() -> Any:
    """Get or create global orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

class TestGetOrchestrator:

    def test_happy_path(self):
        # Happy path: Ensure that an orchestrator is returned
        orchestrator = get_orchestrator()
        assert isinstance(orchestrator, Orchestrator)

    def test_edge_case_none(self):
        # Edge case: Ensure that even if _orchestrator is explicitly set to None, it gets initialized
        global _orchestrator
        _orchestrator = None
        orchestrator = get_orchestrator()
        assert isinstance(orchestrator, Orchestrator)

    def test_error_case_invalid_input(self):
        # Since the function does not take any input, this test case is not applicable
        pass

    def test_async_behavior(self):
        # Since the function does not involve any asynchronous operations, this test case is not applicable
        pass

    def test_multiple_calls(self):
        # Ensure that multiple calls return the same instance
        first_call = get_orchestrator()
        second_call = get_orchestrator()
        assert first_call == second_call

    def test_reset_global(self):
        # Test resetting the global variable and ensure a new instance is created
        global _orchestrator
        original_instance = get_orchestrator()
        _orchestrator = None  # Resetting the global variable
        new_instance = get_orchestrator()
        assert original_instance != new_instance

# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])