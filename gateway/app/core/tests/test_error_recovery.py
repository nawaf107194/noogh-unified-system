import pytest

from gateway.app.core.error_recovery import ErrorRecovery

def test_indent_code_happy_path():
    er = ErrorRecovery()
    code = "def foo():\n    return 'bar'"
    expected = "    def foo():\n        return 'bar'"
    assert er._indent_code(code) == expected

def test_indent_code_edge_case_empty_string():
    er = ErrorRecovery()
    code = ""
    expected = ""
    assert er._indent_code(code) == expected

def test_indent_code_edge_case_none():
    er = ErrorRecovery()
    code = None
    result = er._indent_code(code)
    assert result is None or result == ""

def test_indent_code_edge_case_single_line():
    er = ErrorRecovery()
    code = "print('hello')"
    expected = "    print('hello')"
    assert er._indent_code(code) == expected

def test_indent_code_edge_case_boundary_spaces():
    er = ErrorRecovery()
    spaces = 0
    code = "class Test:\n    def foo(self):\n        pass"
    expected = "\nclass Test:\n    def foo(self):\n        pass"
    assert er._indent_code(code, spaces) == expected

def test_indent_code_error_case_invalid_spaces_type():
    er = ErrorRecovery()
    code = "def bar():\n    return 'baz'"
    with pytest.raises(TypeError):
        er._indent_code(code, spaces="not_an_int")