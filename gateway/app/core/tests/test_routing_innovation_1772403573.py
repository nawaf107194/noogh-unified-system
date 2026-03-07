import pytest

def intelligent_router(task: str):
    """
    Stub router for decoupled Neural Engine mode.
    Always returns None → AgentKernel decides locally.
    """
    return None

# Test cases
@pytest.mark.parametrize("task, expected_output", [
    ("valid_task", None),  # Happy path with a normal input
    (None, None),          # Edge case: input is None
    ("", None),            # Edge case: input is an empty string
    (123, None),           # Edge case: input is an integer
    ([], None),            # Edge case: input is a list
    ({}, None),            # Edge case: input is a dictionary
])
def test_intelligent_router(task, expected_output):
    result = intelligent_router(task)
    assert result == expected_output

# Error cases (none expected in this function)