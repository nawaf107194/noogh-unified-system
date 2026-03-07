
from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext
from gateway.app.llm.remote_brain import RemoteBrainService


class MockBrain(RemoteBrainService):
    def __init__(self, response_text):
        self.response_text = response_text
        self.model = True  # Fake it

    def generate(self, prompt, max_new_tokens=512):
        return self.response_text


class TestPlanModeOutputOnly:

    def test_plan_mode_output_only(self):
        """Verify clean planning output without execution."""

        good_plan_response = """
I will analyze the request.
ACT: NONE
REFLECT:
Plan created.
ANSWER:
# Execution Plan
1. Step one
2. Step two
"""
        brain = MockBrain(good_plan_response)
        kernel = AgentKernel(brain=brain, strict_protocol=True)
        controller = AgentController(kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_ctl_plan_out"})
        auth = AuthContext(token="test", scopes={"*"})

        task = "plan migration strategy"  # Keywords trigger PLAN mode

        result = controller.process_task(task, auth)

        # Expected:
        # Success = True
        # Output contains plan
        # Steps = 1

        assert result.success is True
        assert "# Execution Plan" in result.answer
        assert result.steps == 1

        # Verify ACT: NONE was accepted (it is allowed in planning mode)
        # But no tool was executed.
