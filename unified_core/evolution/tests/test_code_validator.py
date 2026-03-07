import pytest
import ast

def parse_code(code):
    return ast.parse(code)

def get_top_funcs(tree):
    return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

# Test cases
def test_get_top_funcs_happy_path():
    code = """
    def func1():
        pass

    async def func2():
        pass
    """
    tree = parse_code(code)
    funcs = get_top_funcs(tree)
    assert len(funcs) == 2
    assert isinstance(funcs[0], ast.FunctionDef)
    assert isinstance(funcs[1], ast.AsyncFunctionDef)

def test_get_top_funcs_empty_tree():
    code = ""
    tree = parse_code(code)
    funcs = get_top_funcs(tree)
    assert len(funcs) == 0

def test_get_top_funcs_no_functions():
    code = "x = 5"
    tree = parse_code(code)
    funcs = get_top_funcs(tree)
    assert len(funcs) == 0

def test_get_top_funcs_with_classes():
    code = """
    class MyClass:
        def method(self):
            pass
    """
    tree = parse_code(code)
    funcs = get_top_funcs(tree)
    assert len(funcs) == 0

def test_get_top_funcs_with_imports():
    code = """
    import sys
    from os import path
    """
    tree = parse_code(code)
    funcs = get_top_funcs(tree)
    assert len(funcs) == 0

def test_get_top_funcs_with_nested_functions():
    code = """
    def outer():
        def inner():
            pass
    """
    tree = parse_code(code)
    funcs = get_top_funcs(tree)
    assert len(funcs) == 1
    assert isinstance(funcs[0], ast.FunctionDef)

def test_get_top_funcs_invalid_input():
    with pytest.raises(AttributeError):
        get_top_funcs(None)

def test_get_top_funcs_async_behavior():
    code = """
    async def func():
        await some_coroutine()
    """
    tree = parse_code(code)
    funcs = get_top_funcs(tree)
    assert len(funcs) == 1
    assert isinstance(funcs[0], ast.AsyncFunctionDef)