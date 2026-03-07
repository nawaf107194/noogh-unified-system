import pytest
from typing import List, Dict

from unified_core.brain_tools import list_tools, TOOL_REGISTRY

@pytest.fixture
def create_tool_registry():
    original_registry = TOOL_REGISTRY.copy()
    yield {
        "tool1": {"desc": "Description 1", "fn": lambda x: None},
        "tool2": {"desc": "Description 2", "fn": lambda x: None},
    }
    TOOL_REGISTRY.update(original_registry)

def test_happy_path(create_tool_registry):
    """Test normal inputs"""
    expected_output = [
        {"name": "tool1", "description": "Description 1", "function": "lambda"},
        {"name": "tool2", "description": "Description 2", "function": "lambda"}
    ]
    assert list_tools() == expected_output

def test_empty_registry(create_tool_registry):
    """Test with an empty registry"""
    TOOL_REGISTRY.clear()
    assert list_tools() == []

def test_none_registry():
    """Test with None as the registry"""
    global TOOL_REGISTRY
    TOOL_REGISTRY = None
    assert list_tools() is None

def test_boundary_cases(create_tool_registry):
    """Test edge cases like boundaries in a real-world scenario"""
    # Assuming TOOL_REGISTRY can contain a very large number of tools
    for i in range(1000):
        TOOL_REGISTRY[f"tool{i}"] = {"desc": f"Description {i}", "fn": lambda x: None}
    assert len(list_tools()) == 1002  # Including the ones added by create_tool_registry fixture

def test_error_cases():
    """Test error cases (this function does not raise any specific exceptions)"""
    pass