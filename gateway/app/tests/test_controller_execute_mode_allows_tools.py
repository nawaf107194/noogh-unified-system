from unittest.mock import MagicMock


from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext
from gateway.app.llm.remote_brain import RemoteBrainService


class StatefulMockBrain(RemoteBrainService):
    def __init__(self, responses):
        self.responses = responses  # list of strings
        self.call_count = 0
        self.model = True

    def generate(self, prompt, max_new_tokens=512):
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        return self.responses[-1]


class TestExecuteModeAllowsTools:

    def test_execution_mode_allows_tools(self):
        """Verify normal execution works."""

        # Turn 1: Action (No ANSWER block to ensure Action type)
        turn1 = """THINK:
Calculating factorial.
ACT:
```python
print("Factorial: 3628800")
```
"""
        # Turn 2: Final Answer
        turn2 = """THINK:
Done.
ANSWER:
3628800
"""
        brain = StatefulMockBrain([turn1, turn2])
        # Disable persistence to avoid permission errors
        kernel = AgentKernel(brain=brain, strict_protocol=True, enable_persistence=False)

        # Mock tool execution
        kernel.tools.execute_tool = MagicMock(return_value={"success": True, "output": "Factorial: 3628800"})

        controller = AgentController(kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_ctl_exec"})
        auth = AuthContext(token="test", scopes={"*"})

        task = "execute python code to calculate factorial"  # EXECUTE mode with CODE_EXEC capability

        result = controller.process_task(task, auth, mfa_verified=True)

        assert result.success is True
        assert "3628800" in result.answer

        # Verify tool was called
        kernel.tools.execute_tool.assert_called()
        args, kwargs = kernel.tools.execute_tool.call_args
        assert args[0] == "exec_python"
        assert 'print("Factorial: 3628800")' in kwargs["code"]
