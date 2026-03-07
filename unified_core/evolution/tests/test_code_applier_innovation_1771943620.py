import pytest

def detect_indent(code: str) -> int:
    """Detect indentation level of the first def/async def line."""
    for line in code.split('\n'):
        stripped = line.lstrip()
        if stripped.startswith('def ') or stripped.startswith('async def '):
            return len(line) - len(stripped)
    return 0

# Happy path (normal inputs)
def test_detect_indent_happy_path():
    code = """
def my_function(x):
    return x + 1
"""
    assert detect_indent(code) == 4

def test_detect_indent_async_def():
    code = """
async def my_async_function(x):
    return x + 1
"""
    assert detect_indent(code) == 8

# Edge cases (empty, None, boundaries)
def test_detect_indent_empty_string():
    assert detect_indent('') == 0

def test_detect_indent_none_input():
    with pytest.raises(TypeError):
        detect_indent(None)

def test_detect_indent_no_function_definition():
    code = """
x = 5
y = 10
"""
    assert detect_indent(code) == 0

# Error cases (invalid inputs)
def test_detect_indent_invalid_type():
    with pytest.raises(TypeError):
        detect_indent(12345)

# Async behavior (if applicable)
# This function does not have any async functionality, so no additional tests are needed for this.