import pytest
from unittest.mock import patch
from ast import parse, FunctionDef, AsyncFunctionDef

# Assuming the function is part of a module named 'code_applier'
from code_applier import replace_function_in_file

def test_happy_path():
    original_content = """def old_func():\n    pass\n\nother_code()\n"""
    new_code = "def old_func():\n    print('Updated')\n"
    expected_content = """def old_func():\n    print('Updated')\n\nother_code()\n"""
    result = replace_function_in_file(original_content, 'old_func', new_code)
    assert result == expected_content

def test_multiple_matches_first_used():
    original_content = """def target():\n    pass\n\ndef target():\n    pass\n"""
    new_code = "def target():\n    print('Updated')\n"
    expected_content = """def target():\n    print('Updated')\n\ndef target():\n    pass\n"""
    result = replace_function_in_file(original_content, 'target', new_code)
    assert result == expected_content

def test_empty_input():
    result = replace_function_in_file("", "func", "new_code")
    assert result is None

def test_none_input():
    result = replace_function_in_file(None, "func", "new_code")
    assert result is None

def test_no_matching_function():
    original_content = "def some_func():\n    pass\n"
    result = replace_function_in_file(original_content, "nonexistent_func", "new_code")
    assert result is None

def test_invalid_syntax():
    original_content = "def invalid_func():\n  pass\n"  # Indentation error
    result = replace_function_in_file(original_content, "invalid_func", "new_code")
    assert result is None

def test_async_function():
    original_content = """async def async_func():\n    pass\n"""
    new_code = "async def async_func():\n    print('Async updated')\n"
    expected_content = """async def async_func():\n    print('Async updated')\n"""
    result = replace_function_in_file(original_content, 'async_func', new_code)
    assert result == expected_content

def test_async_function_not_replaced():
    original_content = """async def async_func():\n    pass\n"""
    new_code = "def sync_func():\n    print('Sync code')\n"
    result = replace_function_in_file(original_content, 'sync_func', new_code)
    assert result is None

def test_function_at_end_of_file():
    original_content = """def end_func():\n    pass\n"""
    new_code = "def end_func():\n    print('End updated')\n"
    expected_content = """def end_func():\n    print('End updated')\n"""
    result = replace_function_in_file(original_content, 'end_func', new_code)
    assert result == expected_content

def test_function_at_start_of_file():
    original_content = """def start_func():\n    pass\nother_code()\n"""
    new_code = "def start_func():\n    print('Start updated')\n"
    expected_content = """def start_func():\n    print('Start updated')\nother_code()\n"""
    result = replace_function_in_file(original_content, 'start_func', new_code)
    assert result == expected_content

def test_function_with_decorator():
    original_content = """@decorator\ndef decorated_func():\n    pass\n"""
    new_code = "@decorator\ndef decorated_func():\n    print('Decorated updated')\n"
    expected_content = """@decorator\ndef decorated_func():\n    print('Decorated updated')\n"""
    result = replace_function_in_file(original_content, 'decorated_func', new_code)
    assert result == expected_content