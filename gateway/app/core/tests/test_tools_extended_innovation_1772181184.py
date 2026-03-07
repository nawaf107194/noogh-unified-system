import pytest
from gateway.app.core.tools_extended import ToolsExtended

class MockNode:
    def __init__(self, name, args=None, lineno=1, end_lineno=None):
        self.name = name
        self.args = args if args is not None else []
        self.lineno = lineno
        self.end_lineno = end_lineno

@pytest.fixture
def tools_extended():
    return ToolsExtended()

def test_add_function_happy_path(tools_extended):
    node = MockNode("my_func", args=[1, 2], lineno=5, end_lineno=7)
    tools_extended._add_function(node, is_async=False)
    assert len(tools_extended.analysis.functions) == 1
    func_info = tools_extended.analysis.functions[0]
    assert func_info == {
        "name": "my_func",
        "args": 2,
        "line_start": 5,
        "line_end": 7,
        "is_async": False,
        "lines": 3,
    }
    assert tools_extended.analysis.complexity == 1

def test_add_function_empty_args(tools_extended):
    node = MockNode("my_func", args=[], lineno=1, end_lineno=None)
    tools_extended._add_function(node, is_async=False)
    assert len(tools_extended.analysis.functions) == 1
    func_info = tools_extended.analysis.functions[0]
    assert func_info["args"] == 0

def test_add_function_none_args(tools_extended):
    node = MockNode("my_func", args=None, lineno=1, end_lineno=None)
    tools_extended._add_function(node, is_async=False)
    assert len(tools_extended.analysis.functions) == 1
    func_info = tools_extended.analysis.functions[0]
    assert func_info["args"] == 0

def test_add_function_boundary_line_number(tools_extended):
    node = MockNode("my_func", args=[1], lineno=1, end_lineno=None)
    tools_extended._add_function(node, is_async=False)
    assert len(tools_extended.analysis.functions) == 1
    func_info = tools_extended.analysis.functions[0]
    assert func_info["line_start"] == 1
    assert func_info["line_end"] == 1
    assert func_info["lines"] == 1

def test_add_function_async_behavior(tools_extended):
    node = MockNode("my_func", args=[1], lineno=5, end_lineno=7)
    tools_extended._add_function(node, is_async=True)
    assert len(tools_extended.analysis.functions) == 1
    func_info = tools_extended.analysis.functions[0]
    assert func_info["is_async"] == True

def test_add_function_error_case_none_node(tools_extended):
    result = tools_extended._add_function(None, is_async=False)
    assert result is None

def test_add_function_error_case_invalid_args(tools_extended):
    node = MockNode("my_func", args="not a list", lineno=1, end_lineno=None)
    result = tools_extended._add_function(node, is_async=False)
    assert result is None