import pytest

class TestRouter:

    def _is_sensitive(self, prompt: str) -> bool:
        keywords = ["password", "secret", "private key", "ssn", "credit card"]
        return any(k in prompt.lower() for k in keywords)

    @pytest.mark.parametrize("prompt, expected", [
        ("This is a normal message.", False),
        ("The password is 'admin123'.", True),
        ("A secret message.", True),
        ("private key: abcdefg", True),
        ("SSN: 123-45-6789", True),
        ("Credit card number: 1234-5678-1234-5678", True),
    ])
    def test_is_sensitive_happy_path(self, prompt, expected):
        assert self._is_sensitive(prompt) == expected

    @pytest.mark.parametrize("prompt, expected", [
        ("", False),
        (None, False),
        (" ", False),
        ("\t", False),
        ("\n", False),
    ])
    def test_is_sensitive_edge_cases(self, prompt, expected):
        assert self._is_sensitive(prompt) == expected

    @pytest.mark.parametrize("prompt, expected", [
        (12345, False),  # Assuming we don't want to handle non-string inputs
        ([], False),
        ({}, False),
    ])
    def test_is_sensitive_error_cases(self, prompt, expected):
        assert self._is_sensitive(prompt) == expected

# Note: The function _is_sensitive does not have an async behavior.