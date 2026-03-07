import pytest
from neural_engine.execution_enforcer import ExecutionEnforcer

class TestExecutionEnforcer:
    def setup_method(self):
        self.enforcer = ExecutionEnforcer()

    @pytest.mark.parametrize("response, expected", [
        ("step 1 step 2", True),
        ("Step 3 Step 4", True),
        ("خطوة 1 خطوة 2", True),
        ("step 1 خطوة 2", True),
        ("Hello world", False),
        ("step 1", False),
        ("step 2", False),
        ("", False),
        (None, False)
    ])
    def test_has_steps(self, response, expected):
        result = self.enforcer._has_steps(response)
        assert result == expected