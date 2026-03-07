import pytest

class MockToolExecutor:
    TOOL_PATTERN = re.compile(r'\btool\b')

    def get_tool_call_count(self, response: str) -> int:
        """Get number of tool calls in response."""
        return len(self.TOOL_PATTERN.findall(response))

def test_get_tool_call_count_happy_path():
    executor = MockToolExecutor()
    response = "This is a tool call. Another tool call here."
    assert executor.get_tool_call_count(response) == 2

def test_get_tool_call_count_empty_response():
    executor = MockToolExecutor()
    response = ""
    assert executor.get_tool_call_count(response) == 0

def test_get_tool_call_count_none_response():
    executor = MockToolExecutor()
    response = None
    assert executor.get_tool_call_count(response) == 0

def test_get_tool_call_count_boundary_case_single_tool():
    executor = MockToolExecutor()
    response = "This is a single tool call."
    assert executor.get_tool_call_count(response) == 1

def test_get_tool_call_count_boundary_case_no_tools():
    executor = MockToolExecutor()
    response = "No tools here."
    assert executor.get_tool_call_count(response) == 0