"""Tests for code_validator module — AST validation and policy checks."""
import pytest
from unified_core.evolution.code_validator import (
    ast_emission_guard,
    refactor_policy_check,
    structural_integrity_check,
)


class TestAstEmissionGuard:
    """Tests for the AST emission guard."""

    def test_valid_refactoring_passes(self):
        original = "def foo(x):\n    return x + 1"
        refactored = "def foo(x):\n    return x + 2"
        result = ast_emission_guard(original, refactored, {"function": "foo"})
        assert result["pass"] is True

    def test_syntax_error_in_refactored_fails(self):
        original = "def foo(x):\n    return x"
        refactored = "def foo(x)\n    return x"  # Missing colon
        result = ast_emission_guard(original, refactored, {})
        assert result["pass"] is False
        assert "syntax error" in result["reason"].lower()

    def test_function_name_changed_fails(self):
        original = "def foo(x):\n    return x"
        refactored = "def bar(x):\n    return x"
        result = ast_emission_guard(original, refactored, {"function": "foo"})
        assert result["pass"] is False
        assert "FUNC_NAME" in result["reason"]

    def test_function_lost_fails(self):
        original = "def foo(x):\n    return x"
        refactored = "x = 42"
        result = ast_emission_guard(original, refactored, {})
        assert result["pass"] is False
        assert "FUNC_LOST" in result["reason"]

    def test_signature_changed_fails(self):
        original = "def foo(x, y):\n    return x + y"
        refactored = "def foo(x):\n    return x"
        result = ast_emission_guard(original, refactored, {"function": "foo"})
        assert result["pass"] is False
        assert "SIGNATURE" in result["reason"]

    def test_class_added_fails(self):
        original = "def foo():\n    pass"
        refactored = "class Bar:\n    pass\ndef foo():\n    pass"
        result = ast_emission_guard(original, refactored, {"function": "foo"})
        assert result["pass"] is False
        assert "CLASS_ADDED" in result["reason"]

    def test_original_unparseable_passes(self):
        original = "def foo(:\n    bad syntax"
        refactored = "def foo():\n    pass"
        result = ast_emission_guard(original, refactored, {})
        assert result["pass"] is True

    def test_indented_code_handled(self):
        """Class methods should be dedented before parsing."""
        original = "    def method(self):\n        return 1"
        refactored = "    def method(self):\n        return 2"
        result = ast_emission_guard(original, refactored, {"function": "method"})
        assert result["pass"] is True

    def test_target_function_lost_in_refactored(self):
        original = "def target_func():\n    pass\ndef helper():\n    pass"
        refactored = "def renamed():\n    pass\ndef helper():\n    pass"
        result = ast_emission_guard(original, refactored, {"function": "target_func"})
        assert result["pass"] is False
        assert "FUNC_LOST" in result["reason"]

    def test_async_function_preserved(self):
        original = "async def foo(x):\n    return x"
        refactored = "async def foo(x):\n    return x + 1"
        result = ast_emission_guard(original, refactored, {"function": "foo"})
        assert result["pass"] is True


class TestRefactorPolicyCheck:
    """Tests for refactor policy checks."""

    def test_clean_code_passes(self):
        code = "def foo():\n    logger.info('hello')\n    return 42"
        result = refactor_policy_check(code, "test.py", {})
        assert result["pass"] is True

    def test_print_leaks_secret(self):
        code = "def foo(token):\n    print(f'Token: {token}')"
        result = refactor_policy_check(code, "test.py", {})
        assert result["pass"] is False
        assert "SECURITY" in result["reason"]

    def test_print_in_except_block(self):
        code = "def foo():\n    try:\n        x = 1\n    except Exception as e:\n        print(f'Error: {e}')"
        result = refactor_policy_check(code, "test.py", {})
        assert result["pass"] is False
        assert "STYLE" in result["reason"]

    def test_import_inside_method(self):
        code = "def foo():\n    import os\n    return os.getcwd()"
        result = refactor_policy_check(code, "test.py", {})
        assert result["pass"] is False
        assert "import inside method" in result["reason"]

    def test_future_import_allowed(self):
        code = "def foo():\n    from __future__ import annotations\n    return 1"
        result = refactor_policy_check(code, "test.py", {})
        assert result["pass"] is True

    def test_isinstance_noise_detected(self):
        code = (
            "def foo(self):\n"
            "    if not isinstance(self.a, str):\n        pass\n"
            "    if not isinstance(self.b, int):\n        pass\n"
            "    if not isinstance(self.c, float):\n        pass\n"
        )
        result = refactor_policy_check(code, "test.py", {})
        assert result["pass"] is False
        assert "isinstance" in result["reason"]

    def test_indent_drift_detected(self):
        original_code = "    def foo(self):\n        return 1"
        refactored = "def foo(self):\n    return 1"
        result = refactor_policy_check(
            refactored, "test.py",
            {"original_code": original_code}
        )
        assert result["pass"] is False
        assert "INDENT_DRIFT" in result["reason"]


class TestStructuralIntegrityCheck:
    """Tests for structural integrity gate."""

    def test_identical_files_pass(self):
        code = "class Foo:\n    def bar(self):\n        pass"
        result = structural_integrity_check(code, code, "test.py")
        assert result["pass"] is True

    def test_class_count_changed_fails(self):
        original = "class Foo:\n    pass"
        simulated = "class Foo:\n    pass\nclass Bar:\n    pass"
        result = structural_integrity_check(original, simulated, "test.py")
        assert result["pass"] is False
        assert "Class count" in result["reason"]

    def test_method_lost_fails(self):
        original = "class Foo:\n    def bar(self):\n        pass\n    def baz(self):\n        pass"
        simulated = "class Foo:\n    def bar(self):\n        pass"
        result = structural_integrity_check(original, simulated, "test.py")
        assert result["pass"] is False
        assert "Methods lost" in result["reason"]

    def test_method_escaped_to_top_level_fails(self):
        original = "class Foo:\n    def bar(self):\n        pass"
        simulated = "class Foo:\n    pass\ndef bar():\n    pass"
        result = structural_integrity_check(original, simulated, "test.py")
        assert result["pass"] is False

    def test_decorator_lost_fails(self):
        original = "class Foo:\n    @classmethod\n    def bar(cls):\n        pass"
        simulated = "class Foo:\n    def bar(cls):\n        pass"
        result = structural_integrity_check(original, simulated, "test.py")
        assert result["pass"] is False
        assert "decorators lost" in result["reason"]

    def test_syntax_error_in_original_skips(self):
        original = "def foo(:\n    bad"
        simulated = "def foo():\n    pass"
        result = structural_integrity_check(original, simulated, "test.py")
        assert result["pass"] is True

    def test_syntax_error_in_simulated_fails(self):
        original = "def foo():\n    pass"
        simulated = "def foo(:\n    bad"
        result = structural_integrity_check(original, simulated, "test.py")
        assert result["pass"] is False
        assert "syntax error" in result["reason"].lower()

    def test_adding_new_top_level_function_ok(self):
        original = "def foo():\n    pass"
        simulated = "def foo():\n    pass\ndef helper():\n    pass"
        result = structural_integrity_check(original, simulated, "test.py")
        assert result["pass"] is True
