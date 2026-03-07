import pytest

def test_detect_indent_happy_path():
    code = "    def my_function():\n        pass"
    assert detect_indent(code) == 4

def test_detect_indent_async_def():
    code = "    async def my_function():\n        pass"
    assert detect_indent(code) == 4

def test_detect_indent_no_indent():
    code = "def my_function():\n    pass"
    assert detect_indent(code) == 0

def test_detect_indent_multiple_lines():
    code = """
def my_function():
    pass
    async def another_function():
        pass
"""
    assert detect_indent(code) == 0

def test_detect_indent_empty_string():
    code = ""
    assert detect_indent(code) == 0

def test_detect_indent_none_input():
    with pytest.raises(TypeError):
        detect_indent(None)

def test_detect_indent_no_def():
    code = "print('Hello, world!')"
    assert detect_indent(code) == 0

def test_detect_indent_mixed_indentation():
    code = "    def my_function():\n        pass\n    async def another_function():\n        pass"
    assert detect_indent(code) == 4

def test_detect_indent_trailing_whitespace():
    code = "    def my_function(): \n        pass"
    assert detect_indent(code) == 4

def test_detect_indent_with_comments():
    code = "# This is a comment\n    def my_function():\n        pass"
    assert detect_indent(code) == 4

def test_detect_indent_with_multiline_strings():
    code = '"""This is a docstring"""\n    def my_function():\n        pass'
    assert detect_indent(code) == 4