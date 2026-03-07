import pytest
from unified_core.evolution.controller import Controller

# Example function content to use in tests
FUNCTION_CONTENT = """
def example_function():
    print("Hello, World!")
"""

@pytest.fixture
def controller():
    return Controller()

def test_find_function_in_file_happy_path(controller):
    file_content = FUNCTION_CONTENT
    func_name = "example_function"
    result = controller._find_function_in_file(file_content, func_name)
    assert result is not None, f"Function {func_name} should be found"

def test_find_function_in_file_empty_file_content(controller):
    file_content = ""
    func_name = "non_existent_function"
    result = controller._find_function_in_file(file_content, func_name)
    assert result is None, "Empty file content should return None"

def test_find_function_in_file_none_file_content(controller):
    file_content = None
    func_name = "non_existent_function"
    result = controller._find_function_in_file(file_content, func_name)
    assert result is None, "None file content should return None"

def test_find_function_in_file_invalid_func_name(controller):
    file_content = FUNCTION_CONTENT
    func_name = "invalid_function"
    result = controller._find_function_in_file(file_content, func_name)
    assert result is None, f"Non-existent function {func_name} should not be found"

def test_find_function_in_file_boundary_case_single_letter(controller):
    file_content = "def a(): return 1"
    func_name = "a"
    result = controller._find_function_in_file(file_content, func_name)
    assert result is not None, f"Function {func_name} should be found"

def test_find_function_in_file_boundary_case_long_name(controller):
    long_name = "very_very_long_function_name_that_is_quite_unusual"
    file_content = f"def {long_name}(): return 1"
    result = controller._find_function_in_file(file_content, long_name)
    assert result is not None, f"Function {long_name} should be found"