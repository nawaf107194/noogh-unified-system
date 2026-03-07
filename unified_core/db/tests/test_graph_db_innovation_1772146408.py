import pytest

from unified_core.db.graph_db import _sanitize_label, _SAFE_IDENTIFIER

def test_sanitize_label_happy_path():
    # Happy path: normal inputs
    assert _sanitize_label("User") == "User"
    assert _sanitize_label("user_123") == "user_123"
    assert _sanitize_label("Node_Type") == "Node_Type"

def test_sanitize_label_edge_cases():
    # Edge cases: empty string and None
    with pytest.raises(ValueError):
        _sanitize_label("")
    with pytest.raises(ValueError):
        _sanitize_label(None)

def test_sanitize_label_error_cases():
    # Error cases: invalid inputs
    with pytest.raises(ValueError):
        _sanitize_label("User-1")
    with pytest.raises(ValueError):
        _sanitize_label("123")
    with pytest.raises(ValueError):
        _sanitize_label("!@#")

# Async behavior is not applicable for this function as it does not involve any I/O or external systems.