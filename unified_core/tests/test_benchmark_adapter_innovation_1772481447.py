import pytest

class BenchmarkAdapter:
    def __init__(self, tool_selection_correct: int = 0, tool_selection_total: int = 0):
        self.tool_selection_correct = tool_selection_correct
        self.tool_selection_total = tool_selection_total

    def selection_accuracy(self) -> float:
        if self.tool_selection_total == 0:
            return 0.0
        return self.tool_selection_correct / self.tool_selection_total

# Happy path (normal inputs)
def test_selection_accuracy_happy_path():
    adapter = BenchmarkAdapter(tool_selection_correct=5, tool_selection_total=10)
    assert adapter.selection_accuracy() == 0.5

# Edge cases (empty, None, boundaries)
def test_selection_accuracy_zero_total():
    adapter = BenchmarkAdapter(tool_selection_correct=5, tool_selection_total=0)
    assert adapter.selection_accuracy() == 0.0

def test_selection_accuracy_empty_input():
    adapter = BenchmarkAdapter()
    assert adapter.selection_accuracy() == 0.0

# Error cases (invalid inputs) - Not applicable as the function does not raise exceptions for invalid inputs