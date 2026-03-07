import pytest
from unified_core.evolution.code_applier import find_function_in_file

def test_find_function_in_file_happy_path():
    file_content = """
def foo(x):
    return x * 2

class Bar:
    def baz(self, y):
        return y + 3
"""
    assert find_function_in_file(file_content, 'foo') == "def foo(x):\n    return x * 2"
    assert find_function_in_file(file_content, 'baz') == "    def baz(self, y):\n        return y + 3"

def test_find_function_in_file_edge_cases():
    file_content = ""
    assert find_function_in_file(file_content, 'foo') is None

    file_content = "x = 5"
    assert find_function_in_file(file_content, 'foo') is None

    file_content = """
def foo(x):
    return x * 2
"""
    assert find_function_in_file(file_content, 'foo') == "def foo(x):\n    return x * 2"

def test_find_function_in_file_error_cases():
    file_content = "import sys"
    assert find_function_in_file(file_content, 'foo') is None

def test_find_function_in_file_async_behavior():
    file_content = """
async def async_foo(x):
    return x * 2
"""
    assert find_function_in_file(file_content, 'async_foo') == "async def async_foo(x):\n    return x * 2"