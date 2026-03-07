"""Tests for code_applier module — file manipulation utilities."""
import pytest
from unified_core.evolution.code_applier import (
    detect_indent,
    reindent,
    find_function_in_file,
    replace_function_in_file,
)


class TestDetectIndent:
    def test_zero_indent(self):
        assert detect_indent("def foo():\n    pass") == 0

    def test_four_indent(self):
        assert detect_indent("    def foo():\n        pass") == 4

    def test_eight_indent(self):
        assert detect_indent("        def foo():\n            pass") == 8

    def test_async_def(self):
        assert detect_indent("    async def foo():\n        pass") == 4

    def test_no_def(self):
        assert detect_indent("x = 1\ny = 2") == 0


class TestReindent:
    def test_no_change_needed(self):
        code = "def foo():\n    pass"
        assert reindent(code, 0) == code

    def test_add_indent(self):
        code = "def foo():\n    pass"
        result = reindent(code, 4)
        assert result.startswith("    def foo():")
        assert "\n        pass" in result

    def test_remove_indent(self):
        code = "    def foo():\n        pass"
        result = reindent(code, 0)
        assert result.startswith("def foo():")
        assert "\n    pass" in result

    def test_preserves_empty_lines(self):
        code = "def foo():\n\n    pass"
        result = reindent(code, 4)
        lines = result.split('\n')
        # Empty line should remain empty
        assert lines[1] == "" or lines[1].strip() == ""


class TestFindFunction:
    SAMPLE_FILE = (
        "import os\n\n"
        "def alpha():\n    return 1\n\n"
        "def beta(x, y):\n    return x + y\n\n"
        "class MyClass:\n    def method(self):\n        pass\n"
    )

    def test_find_top_level_function(self):
        result = find_function_in_file(self.SAMPLE_FILE, "alpha")
        assert result is not None
        assert "return 1" in result

    def test_find_second_function(self):
        result = find_function_in_file(self.SAMPLE_FILE, "beta")
        assert result is not None
        assert "return x + y" in result

    def test_find_class_method(self):
        result = find_function_in_file(self.SAMPLE_FILE, "method")
        assert result is not None
        assert "self" in result

    def test_not_found_returns_none(self):
        assert find_function_in_file(self.SAMPLE_FILE, "nonexistent") is None

    def test_syntax_error_returns_none(self):
        assert find_function_in_file("def bad(:\n    oops", "bad") is None


class TestReplaceFunction:
    SAMPLE_FILE = "def foo():\n    return 1\n\ndef bar():\n    return 2\n"

    def test_replace_first_function(self):
        result = replace_function_in_file(
            self.SAMPLE_FILE, "foo", "def foo():\n    return 99"
        )
        assert result is not None
        assert "return 99" in result
        assert "return 2" in result  # bar unchanged

    def test_replace_second_function(self):
        result = replace_function_in_file(
            self.SAMPLE_FILE, "bar", "def bar():\n    return 42"
        )
        assert result is not None
        assert "return 42" in result
        assert "return 1" in result  # foo unchanged

    def test_replace_nonexistent_returns_none(self):
        assert replace_function_in_file(self.SAMPLE_FILE, "baz", "def baz(): pass") is None

    def test_replace_syntax_error_returns_none(self):
        assert replace_function_in_file("def bad(:\n  x", "bad", "def bad(): pass") is None

    def test_preserves_code_before_and_after(self):
        code = "# header\ndef target():\n    pass\n# footer\n"
        result = replace_function_in_file(code, "target", "def target():\n    return True")
        assert result is not None
        assert "# header" in result
        assert "# footer" in result
        assert "return True" in result
