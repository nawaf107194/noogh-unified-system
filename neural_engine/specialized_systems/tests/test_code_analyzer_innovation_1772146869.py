import pytest
from ast import parse, NodeTransformer, walk
from typing import List, Dict, Any

from neural_engine.specialized_systems.code_analyzer import extract_classes

class TestExtractClasses:
    def test_happy_path(self):
        # Sample Python code with multiple classes
        code = """
class MyClass:
    def method1(self):
        pass

class AnotherClass:
    async def async_method(self):
        pass
"""
        tree = parse(code)
        
        result = extract_classes(tree)
        expected = [
            {
                "name": "MyClass",
                "line": 2,
                "bases": ["object"],
                "methods": ["method1"],
                "docstring": None,
            },
            {
                "name": "AnotherClass",
                "line": 5,
                "bases": ["object"],
                "methods": ["async_method"],
                "docstring": None,
            }
        ]
        
        assert result == expected

    def test_edge_case_empty(self):
        # Empty code
        tree = parse("")
        
        result = extract_classes(tree)
        expected = []
        
        assert result == expected

    def test_edge_case_none(self):
        # Input is None
        with pytest.raises(TypeError) as exc_info:
            extract_classes(None)
        
        assert "Argument 'tree' must be an AST node" in str(exc_info.value)

    def test_error_case_invalid_input(self):
        # Invalid input type (not an AST node)
        with pytest.raises(TypeError) as exc_info:
            extract_classes("not_an_ast_node")
        
        assert "Argument 'tree' must be an AST node" in str(exc_info.value)

    def test_async_behavior(self):
        # Code with async method
        code = """
class AsyncClass:
    async def async_method(self):
        pass
"""
        tree = parse(code)
        
        result = extract_classes(tree)
        expected = [
            {
                "name": "AsyncClass",
                "line": 2,
                "bases": ["object"],
                "methods": ["async_method"],
                "docstring": None,
            }
        ]
        
        assert result == expected

    def test_with_bases(self):
        # Class with bases
        code = """
class DerivedClass(Base1, Base2):
    def method(self):
        pass
"""
        tree = parse(code)
        
        result = extract_classes(tree)
        expected = [
            {
                "name": "DerivedClass",
                "line": 2,
                "bases": ["Base1", "Base2"],
                "methods": ["method"],
                "docstring": None,
            }
        ]
        
        assert result == expected

    def test_with_docstring(self):
        # Class with docstring
        code = """
class MyClass:
    '''This is a docstring'''
    
    def method1(self):
        pass
"""
        tree = parse(code)
        
        result = extract_classes(tree)
        expected = [
            {
                "name": "MyClass",
                "line": 2,
                "bases": ["object"],
                "methods": ["method1"],
                "docstring": "This is a docstring",
            }
        ]
        
        assert result == expected