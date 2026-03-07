
import pytest

from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext


# Mock Brain that follows protocol
class MockBrain:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    def generate(self, prompt, max_new_tokens=512):
        # Return pre-scripted response based on call count or prompt content
        # For simplicity, we just pop from list
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return "THINK:\nI am out of ideas.\nACT:\nNONE\nREFLECT:\nStalled.\n"  # Default stall


@pytest.fixture
def workspace_setup(tmp_path):
    # Setup - use a tmp dir as workspace
    return tmp_path


@pytest.fixture
def service_auth():
    return AuthContext(
        token="service", scopes={"tools:use", "http:request", "fs:read", "fs:write", "memory:rw", "exec"}
    )


def test_calculator_protocol_flow(service_auth):
    """
    Test a simple calculation task.
    Verifies: THINK -> ACT (exec_python) -> REFLECT -> ANSWER
    """
    # Define script
    script = [
        # Step 1: Reason and Act
        """THINK:
I need to calculate the factorial of 5 using python.
ACT:
```python
import math
print(f"Result: {math.factorial(5)}")
```
REFLECT:
I have executed the code. Now I will check the result in the next step.""",
        # Step 2: Observe and Answer
        """THINK:
The code executed successfully and printed 'Result: 120'. Use this answer.
ACT:
NONE
REFLECT:
Task complete.
ANSWER:
120""",
    ]

    brain = MockBrain(script)
    kernel = AgentKernel(brain=brain, max_iterations=5)

    result = kernel.process("Calculate factorial of 5", auth=service_auth)

    assert result.success is True
    assert "120" in result.answer
    assert result.steps == 2


def test_file_operations(workspace_setup, service_auth):
    """
    Test file writing and reading.
    Verifies: write_file -> read_file
    """
    test_file = workspace_setup / "monitor.txt"
    path_str = str(test_file)

    script = [
        # Step 1: Write file
        f"""THINK:
I write 'System OK' to the file.
ACT:
write_file(path="{path_str}", content="System OK")
REFLECT:
File written.""",
        # Step 2: Read file
        f"""THINK:
Now I verify the file content.
ACT:
read_file(path="{path_str}")
REFLECT:
Content is 'System OK'. Task done.
ANSWER:
System OK""",
    ]

    brain = MockBrain(script)
    kernel = AgentKernel(brain=brain)

    # Patch AgentSkills directly to use the workspace
    from gateway.app.core.skills import AgentSkills

    # Save old root
    old_root = getattr(AgentSkills, "SAFE_ROOT", None)
    try:
        # We must allow the parent dir of the test file, which is workspace_setup
        AgentSkills.SAFE_ROOT = str(workspace_setup)

        result = kernel.process("Create monitor file", auth=service_auth)

        if not result.success:
            print(f"FAILED RESULT: {result}")
            print(f"MEMORY: {kernel.get_memory_context()}")

        assert result.success is True
        assert test_file.exists()
        assert test_file.read_text() == "System OK"
    finally:
        if old_root:
            AgentSkills.SAFE_ROOT = old_root


def test_budget_enforcement(service_auth):
    """
    Test that the agent stops when budget is exceeded.
    """
    # We will simulate a loop that wastes time/steps
    script = [
        """THINK: Wasting time 1.\nACT: NONE\nREFLECT: Continue.""",
        """THINK: Wasting time 2.\nACT: NONE\nREFLECT: Continue.""",
        """THINK: Wasting time 3.\nACT: NONE\nREFLECT: Continue.""",
    ]

    brain = MockBrain(script)
    # Set very low budget
    kernel = AgentKernel(brain=brain, max_iterations=2)

    result = kernel.process("Waste time", auth=service_auth)

    assert result.success is False
    assert result.error == "Max iterations limit"
    assert "maximum iterations reached" in result.answer.lower()


def test_insufficient_scope():
    """Test that capabilities are denied without scope"""
    readonly_auth = AuthContext(token="readonly", scopes={"read:status"})

    script = [
        """THINK: Try to write file.\nACT: write_file(path="hack.txt", content="hacked")\nREFLECT: Check result."""
    ]

    brain = MockBrain(script)
    kernel = AgentKernel(brain=brain)

    result = kernel.process("Try hacking", auth=readonly_auth)

    # The kernel returns immediately upon auth failure!
    # It does not continue the loop.

    assert result.success is False
    assert result.error == "CapabilityBoundaryViolation"
    assert "UNAUTHORIZED" in result.answer


def test_conversational_fallback():
    """Test that plain text responses result in safe timeout (thought loop)"""
    # The agent interprets plain text as 'Thinking'.
    # Since it never Acts or Answers, it should hit max iterations.
    script = ["Hello! I am ready to help."] * 6  # Provide enough frames

    brain = MockBrain(script)
    kernel = AgentKernel(brain=brain)

    result = kernel.process("Hi", auth=AuthContext(token="test", scopes={"*"}))

    # Due to auto-THINK injection, "Hello!" becomes "THINK: Hello!", which is valid protocol.
    # The agent loops thinking "Hello!" until max iterations.
    assert result.success is False
    assert result.error == "Max iterations limit"


if __name__ == "__main__":
    pytest.main([__file__])
