import pytest

from gateway.app.core.protocol import generate_correction_prompt

def test_generate_correction_prompt_happy_path():
    violations = ("Violation 1", "Violation 2")
    expected_output = """ERROR: Protocol violation(s) detected:
Violation 1
Violation 2
Please follow THINK -> ACT -> REFLECT -> ANSWER format."""
    assert generate_correction_prompt(violations) == expected_output

def test_generate_correction_prompt_empty_violations():
    violations = ()
    expected_output = """ERROR: Protocol violation(s) detected:

Please follow THINK -> ACT -> REFLECT -> ANSWER format."""
    assert generate_correction_prompt(violations) == expected_output

def test_generate_correction_prompt_none_violations():
    violations = None
    expected_output = """ERROR: Protocol violation(s) detected:None
Please follow THINK -> ACT -> REFLECT -> ANSWER format."""
    assert generate_correction_prompt(violations) == expected_output

def test_generate_correction_prompt_single_violation():
    violations = ("Single Violation",)
    expected_output = """ERROR: Protocol violation(s) detected:
Single Violation
Please follow THINK -> ACT -> REFLECT -> ANSWER format."""
    assert generate_correction_prompt(violations) == expected_output