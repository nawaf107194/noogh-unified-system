import pytest

def _replace_unicode_escape(m):
    try:
        return chr(int(m.group(1), 16))
    except (ValueError, OverflowError):
        return m.group(0)

@pytest.mark.parametrize("input_str, expected_output", [
    ("\\u0048", "H"),  # Happy path: normal input
    ("\\u003F", "?"),   # Happy path: another normal input
    ("\\uFFFF", "\uFFFF"),  # Boundary case: maximum Unicode value
    ("", ""),  # Edge case: empty string
    (None, None),  # Edge case: None input
    ("not a unicode escape", "not a unicode escape")  # Edge case: no unicode escape
])
def test_replace_unicode_escape(input_str, expected_output):
    result = _replace_unicode_escape(input_str)
    assert result == expected_output

@pytest.mark.parametrize("input_str", [
    "\\uGHIJ",  # Error case: invalid input (non-hex value)
    "\\u1234567890abcdef",  # Error case: valid hex but exceeds Unicode range
])
def test_replace_unicode_escape_error(input_str):
    result = _replace_unicode_escape(input_str)
    assert result == input_str