import pytest

class TestExecutionEnforcer:
    @pytest.fixture
    def enforcer(self):
        from neural_engine.execution_enforcer import ExecutionEnforcer
        return ExecutionEnforcer()

    def test_happy_path(self, enforcer):
        """Normal inputs should be correctly classified"""
        assert enforcer._is_execution("This is a normal response.") == True
        assert enforcer._is_execution("No forbidden words here!") == True

    @pytest.mark.parametrize("input_data", [
        (""),
        (None),
        ("\t "),
        ("  \n  ")
    ])
    def test_edge_cases(self, enforcer, input_data):
        """Empty, None, and whitespace inputs should be correctly classified"""
        assert enforcer._is_execution(input_data) == False

    @pytest.mark.parametrize("input_data", [
        "This is a",
        "Represents the answer.",
        "This test is correct.",
        "Evaluation result."
    ])
    def test_forbidden_words(self, enforcer, input_data):
        """Inputs containing forbidden words should be correctly classified"""
        assert not enforcer._is_execution(input_data) == True