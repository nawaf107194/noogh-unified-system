import pytest
from unified_core.evolution.code_validator import refactor_policy_check

def test_happy_path():
    refactored_code = """
def foo():
    pass
"""
    target_file = "example.py"
    metadata = {
        "function": "foo",
        "target": "example.py"
    }
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": True, "reason": "Policy check passed"}

def test_no_token_leakage():
    refactored_code = """
print('This is a token')
"""
    target_file = "example.py"
    metadata = {
        "function": "foo",
        "target": "example.py"
    }
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": False, "violations": ["SECURITY: print() leaks sensitive value (matched: r'print\\s*\(.*(?:token|auth|secret|password|key|bearer).*\)')"]}

def test_import_inside_method_body():
    refactored_code = """
def foo():
    import os
"""
    target_file = "example.py"
    metadata = {
        "function": "foo",
        "target": "example.py"
    }
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": False, "violations": ["STYLE: import inside function foo(): 'os' — move to top level"]}

def test_isinstance_noise():
    refactored_code = """
class MyClass:
    def __init__(self):
        if not isinstance(self.value, str):
            pass
"""
    target_file = "example.py"
    metadata = {
        "function": "__init__",
        "target": "example.py"
    }
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": False, "violations": ["NOISE: 1 redundant isinstance checks on typed fields"]}

def test_scope_change():
    refactored_code = """
class MyClass:
    def foo(self):
        pass
"""
    target_file = "example.py"
    metadata = {
        "function": "foo",
        "target": "example.py"
    }
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": False, "violations": ["SCOPE: method refactored to top-level (def with 0 indent)"]}

def test_indentation_drift():
    original_code = """
class MyClass:
    def foo(self):
        pass
"""
    refactored_code = """
def foo():
    pass
"""
    target_file = "example.py"
    metadata = {
        "function": "foo",
        "target": "example.py",
        "original_code": original_code
    }
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": False, "violations": ["INDENT_DRIFT: original def at col 4, refactored at col 0 (scope narrowed)"]}

def test_empty_input():
    refactored_code = ""
    target_file = "example.py"
    metadata = {
        "function": "",
        "target": "example.py"
    }
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": True, "reason": "Policy check passed"}

def test_none_input():
    refactored_code = None
    target_file = "example.py"
    metadata = {
        "function": None,
        "target": "example.py"
    }
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": True, "reason": "Policy check passed"}

def test_metadata_none_input():
    refactored_code = """
def foo():
    pass
"""
    target_file = "example.py"
    metadata = None
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": True, "reason": "Policy check passed"}

def test_metadata_empty_input():
    refactored_code = """
def foo():
    pass
"""
    target_file = "example.py"
    metadata = {}
    result = refactor_policy_check(refactored_code, target_file, metadata)
    assert result == {"pass": True, "reason": "Policy check passed"}