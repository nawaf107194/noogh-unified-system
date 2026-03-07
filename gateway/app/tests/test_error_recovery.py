"""
Tests for Error Recovery System.
Tests error parsing, fix suggestions, and integration with AgentKernel.
"""

import pytest

from gateway.app.core.error_recovery import ErrorParser, ParsedError


class TestErrorParser:
    """Test error parsing functionality"""

    @pytest.fixture
    def parser(self):
        return ErrorParser()

    def test_parse_name_error(self, parser):
        """Parse NameError correctly"""
        error = "NameError: name 'undefined_var' is not defined"
        parsed = parser.parse(error)

        assert parsed.error_type == "NameError"
        assert "undefined_var" in parsed.message

    def test_parse_file_not_found(self, parser):
        """Parse FileNotFoundError"""
        error = "FileNotFoundError: [Errno 2] No such file or directory: 'missing.txt'"
        parsed = parser.parse(error)

        assert parsed.error_type == "FileNotFoundError"
        assert "missing.txt" in parsed.message

    def test_parse_type_error(self, parser):
        """Parse TypeError"""
        error = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        parsed = parser.parse(error)

        assert parsed.error_type == "TypeError"
        assert "unsupported operand" in parsed.message

    def test_parse_with_line_number(self, parser):
        """Extract line number from traceback"""
        error = """Traceback (most recent call last):
  File "<string>", line 3, in <module>
NameError: name 'x' is not defined"""
        parsed = parser.parse(error)

        assert parsed.line_number == 3
        assert parsed.error_type == "NameError"

    def test_suggest_fixes_name_error(self, parser):
        """Suggest fixes for NameError"""
        parsed = ParsedError(
            error_type="NameError",
            message="name 'math' is not defined",
            original="NameError: name 'math' is not defined",
        )

        fixes = parser.suggest_fixes(parsed)

        assert len(fixes) > 0
        assert any("import" in fix.lower() for fix in fixes)

    def test_suggest_fixes_file_error(self, parser):
        """Suggest fixes for FileNotFoundError"""
        parsed = ParsedError(
            error_type="FileNotFoundError",
            message="No such file or directory: 'data.txt'",
            original="FileNotFoundError...",
        )

        fixes = parser.suggest_fixes(parsed)

        assert len(fixes) > 0
        assert any("exists" in fix for fix in fixes)

    def test_suggest_fixes_unknown_error(self, parser):
        """Generic fixes for unknown errors"""
        parsed = ParsedError(
            error_type="WeirdError", message="Something went wrong", original="WeirdError: Something went wrong"
        )

        fixes = parser.suggest_fixes(parsed)

        # Should return generic fixes
        assert len(fixes) > 0

    def test_generate_fix_code_name_error(self, parser):
        """Generate fix code for NameError"""
        original = "result = math.sqrt(16)"
        parsed = ParsedError(error_type="NameError", message="name 'math' is not defined", original="...")

        fixed = parser.generate_fix_code(original, parsed)

        assert fixed is not None
        assert "import math" in fixed
        assert original in fixed

    def test_format_error_report(self, parser):
        """Format error report with fixes"""
        parsed = ParsedError(
            error_type="ValueError", message="invalid literal for int()", line_number=5, original="..."
        )
        fixes = ["Check input type", "Use try/except"]

        report = parser.format_error_report(parsed, fixes)

        assert "ERROR ANALYSIS" in report
        assert "ValueError" in report
        assert "Line: 5" in report
        assert "Check input type" in report
        assert "Use try/except" in report


class TestErrorRecoveryPatterns:
    """Test error patterns and recovery suggestions"""

    @pytest.fixture
    def parser(self):
        return ErrorParser()

    def test_zero_division_error(self, parser):
        """Handle ZeroDivisionError"""
        error = "ZeroDivisionError: division by zero"
        parsed = parser.parse(error)
        fixes = parser.suggest_fixes(parsed)

        assert parsed.error_type == "ZeroDivisionError"
        assert any("zero" in fix.lower() for fix in fixes)

    def test_index_error(self, parser):
        """Handle IndexError"""
        error = "IndexError: list index out of range"
        parsed = parser.parse(error)
        fixes = parser.suggest_fixes(parsed)

        assert parsed.error_type == "IndexError"
        assert any("length" in fix.lower() or "len" in fix for fix in fixes)

    def test_key_error(self, parser):
        """Handle KeyError"""
        error = "KeyError: 'missing_key'"
        parsed = parser.parse(error)
        fixes = parser.suggest_fixes(parsed)

        assert parsed.error_type == "KeyError"
        assert any("get()" in fix or "in dict" in fix for fix in fixes)

    def test_attribute_error(self, parser):
        """Handle AttributeError"""
        error = "AttributeError: 'str' object has no attribute 'append'"
        parsed = parser.parse(error)
        fixes = parser.suggest_fixes(parsed)

        assert parsed.error_type == "AttributeError"
        assert any("hasattr" in fix or "type" in fix.lower() for fix in fixes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
