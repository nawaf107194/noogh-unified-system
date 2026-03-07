import pytest
from unified_core.dependency_graph_generator import DependencyGraphGenerator

def test_parse_module_happy_path():
    generator = DependencyGraphGenerator()
    result = generator.parse_module("example.py")
    assert isinstance(result, list)
    assert all(isinstance(item, str) for item in result)

def test_parse_module_empty_file():
    with open("empty_file.py", "w") as f:
        pass
    generator = DependencyGraphGenerator()
    result = generator.parse_module("empty_file.py")
    assert result == []

def test_parse_module_none_input():
    generator = DependencyGraphGenerator()
    result = generator.parse_module(None)
    assert result is None

def test_parse_module_invalid_path():
    generator = DependencyGraphGenerator()
    result = generator.parse_module("non_existent_file.py")
    assert result is None