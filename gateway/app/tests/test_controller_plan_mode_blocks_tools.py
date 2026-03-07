

from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext
from gateway.app.llm.remote_brain import RemoteBrainService


class MockBrain(RemoteBrainService):
    def __init__(self, response_text):
        self.response_text = response_text
        self.model = True

    def generate(self, prompt, max_new_tokens=512):
        return self.response_text


class TestPlanModeBlocksTools:

    def test_plan_mode_blocks_tools(self):
        """
        Verify that if the LLM tries to ACT in planning mode, it causes a ProtocolViolation.
        """
        # malicious_response attempts to exec_python
        # Use DEDENTED string with correct THINK block
        malicious_response = """THINK:
Need to hack system to plan better.
ACT:
```python
print("hack")
```
REFLECT:
Done.
ANSWER:
Hacked.
"""
        # Setup specific brain
        brain = MockBrain(malicious_response)
        # Disable persistence
        kernel = AgentKernel(brain=brain, strict_protocol=True, enable_persistence=False)

        controller = AgentController(kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_ctl_plan_block"})
        auth = AuthContext(token="test", scopes={"*"})

        task = "plan system architecture"

        # This should trigger planning mode
        result = controller.process_task(task, auth)

        # Expected:
        # Fails due to protocol violation (ACT prohibited) -> Fallback -> Success=True
        assert result.success is True
        assert result.metadata.get("fallback_used") is True
        assert (
            "PROTOCOL_VIOLATION" in result.metadata["error_type"]
            or "PROTOCOL_FALLBACK" in result.metadata["error_type"]
        )

        # Verify violation detail mentions ACT not allowed
        if result.metadata.get("original_error"):
            assert "not allowed" in result.metadata["original_error"] or "Actions not allowed" in str(
                result.metadata.get("original_error")
            )
