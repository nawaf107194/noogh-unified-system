import pytest

class TestCognitiveTrace:
    def setup_method(self):
        from neural_engine.cognitive_trace import CognitiveTrace
        self.trace = CognitiveTrace()

    def test_start_iteration_happy_path(self):
        """Test normal iteration start."""
        self.trace.start_iteration(1)
        assert self.trace.iterations == 2
        assert self.trace.events == [{'type': 'ITERATION_START', 'data': {'iteration': 2}}]

    def test_start_iteration_edge_case_zero(self):
        """Test edge case with zero iteration number."""
        self.trace.start_iteration(0)
        assert self.trace.iterations == 1
        assert self.trace.events == [{'type': 'ITERATION_START', 'data': {'iteration': 1}}]

    def test_start_iteration_edge_case_negative(self):
        """Test edge case with negative iteration number."""
        self.trace.start_iteration(-1)
        assert self.trace.iterations == 0
        assert self.trace.events == []

    def test_start_iteration_error_case_invalid_input_type(self):
        """Test error case with invalid input type (non-integer)."""
        with pytest.raises(TypeError, match="iteration_num must be an integer"):
            self.trace.start_iteration("not_an_integer")

    def test_start_iteration_error_case_none(self):
        """Test error case with None input."""
        with pytest.raises(TypeError, match="iteration_num must be an integer"):
            self.trace.start_iteration(None)

    def test_start_iteration_error_case_float(self):
        """Test error case with float input."""
        with pytest.raises(TypeError, match="iteration_num must be an integer"):
            self.trace.start_iteration(3.14)