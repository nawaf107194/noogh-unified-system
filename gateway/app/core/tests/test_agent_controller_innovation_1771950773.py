import pytest
from gateway.app.core.agent_controller import AgentController

@pytest.fixture
def agent_controller():
    return AgentController()

# Happy path (normal inputs)
def test_sanitize_task_input_happy_path(agent_controller):
    input_task = """
    === POLICY DEBUG ===
    Matched Triggers:
    Required Capabilities: READ, WRITE
    Forbidden Capabilities: DELETE
    Simulated PolicyEngine.decide()
    Intent: DO_SOMETHING
    Reason: Allowed
    Confidence: 90%
    Some actual task content...
    """
    expected_output = "Some actual task content..."
    assert agent_controller._sanitize_task_input(input_task) == expected_output

# Edge cases (empty, None)
def test_sanitize_task_input_empty(agent_controller):
    input_task = ""
    expected_output = ""
    assert agent_controller._sanitize_task_input(input_task) == expected_output

def test_sanitize_task_input_none(agent_controller):
    input_task = None
    assert agent_controller._sanitize_task_input(input_task) is None

# Error cases (invalid inputs)
def test_sanitize_task_input_invalid_type(agent_controller):
    input_task = 12345
    assert agent_controller._sanitize_task_input(input_task) is None