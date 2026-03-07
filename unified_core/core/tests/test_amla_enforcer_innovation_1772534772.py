import pytest
from unified_core.core.amla_enforcer import is_strict_mode

def test_is_strict_mode_happy_path():
    """Test the happy path where the function returns True as expected"""
    assert is_strict_mode() is True