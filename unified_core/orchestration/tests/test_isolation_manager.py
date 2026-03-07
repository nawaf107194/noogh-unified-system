import pytest

from unified_core.orchestration.isolation_manager import IsolationManager

# Happy path (normal inputs)
def test_get_status_happy_path():
    isolation_manager = IsolationManager(sandbox_available=True, lab_container_available=False, TOOL_ISOLATION_POLICY=['policy1', 'policy2'])
    assert isolation_manager.get_status() == {
        "sandbox_available": True,
        "lab_container_available": False,
        "policy_tools": 2
    }

# Edge cases (empty, None, boundaries)
def test_get_status_empty_policy():
    isolation_manager = IsolationManager(sandbox_available=True, lab_container_available=False, TOOL_ISOLATION_POLICY=[])
    assert isolation_manager.get_status() == {
        "sandbox_available": True,
        "lab_container_available": False,
        "policy_tools": 0
    }

def test_get_status_none_policy():
    isolation_manager = IsolationManager(sandbox_available=True, lab_container_available=False, TOOL_ISOLATION_POLICY=None)
    assert isolation_manager.get_status() == {
        "sandbox_available": True,
        "lab_container_available": False,
        "policy_tools": 0
    }

# Error cases (invalid inputs) ONLY IF the code explicitly raises them
# This function does not raise any exceptions, so no error case tests are needed

# Async behavior (if applicable)
# This function is synchronous, so no async behavior tests are needed