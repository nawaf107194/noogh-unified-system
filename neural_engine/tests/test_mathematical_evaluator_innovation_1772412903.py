import pytest

class MockStep:
    def __init__(self, step_number, verification=None):
        self.step_number = step_number
        self.verification = verification

def test_check_step_verification_happy_path():
    steps = [
        MockStep(1, True),
        MockStep(2, True),
        MockStep(3, True)
    ]
    result = _check_step_verification(steps)
    assert result == {"all_verified": True, "unverified": []}

def test_check_step_verification_empty_steps():
    steps = []
    result = _check_step_verification(steps)
    assert result == {"all_verified": True, "unverified": []}

def test_check_step_verification_none_steps():
    result = _check_step_verification(None)
    assert result == {"all_verified": False, "unverified": []}

def test_check_step_verification_unverified_steps():
    steps = [
        MockStep(1, True),
        MockStep(2, False),
        MockStep(3, True)
    ]
    result = _check_step_verification(steps)
    assert result == {"all_verified": False, "unverified": [2]}