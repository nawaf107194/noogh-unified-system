import pytest

def test_run_tests_happy_path():
    from gateway.app.core.skills import run_tests
    result = run_tests(test_path="./tests")
    assert result == {
        "success": False, 
        "error": "SECURITY_BLOCKED: run_tests() disabled. Use ProcessActuator.spawn() for subprocess execution.",
        "blocked_reason": "Direct subprocess bypasses ALLOWED_COMMANDS allowlist"
    }

def test_run_tests_edge_case_empty_string():
    from gateway.app.core.skills import run_tests
    result = run_tests(test_path="")
    assert result == {
        "success": False, 
        "error": "SECURITY_BLOCKED: run_tests() disabled. Use ProcessActuator.spawn() for subprocess execution.",
        "blocked_reason": "Direct subprocess bypasses ALLOWED_COMMANDS allowlist"
    }

def test_run_tests_edge_case_none():
    from gateway.app.core.skills import run_tests
    result = run_tests(test_path=None)
    assert result == {
        "success": False, 
        "error": "SECURITY_BLOCKED: run_tests() disabled. Use ProcessActuator.spawn() for subprocess execution.",
        "blocked_reason": "Direct subprocess bypasses ALLOWED_COMMANDS allowlist"
    }

def test_run_tests_invalid_input_type():
    from gateway.app.core.skills import run_tests
    result = run_tests(test_path=123)
    assert result == {
        "success": False, 
        "error": "SECURITY_BLOCKED: run_tests() disabled. Use ProcessActuator.spawn() for subprocess execution.",
        "blocked_reason": "Direct subprocess bypasses ALLOWED_COMMANDS allowlist"
    }