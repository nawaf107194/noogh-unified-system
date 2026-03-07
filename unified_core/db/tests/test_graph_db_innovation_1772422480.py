import pytest

from unified_core.db.graph_db import _sanitize_rel_type, _SAFE_IDENTIFIER

@pytest.mark.parametrize("rel_type, expected", [
    ("valid_type", "valid_type"),
    ("AnotherValidType123", "AnotherValidType123"),
    ("_underscore", "_underscore")
])
def test_sanitize_rel_type_happy_path(rel_type, expected):
    assert _sanitize_rel_type(rel_type) == expected

@pytest.mark.parametrize("rel_type", [
    "",
    None,
    " ",
    "@invalid",
    "invalid-type!",
    "123start"
])
def test_sanitize_rel_type_edge_cases(rel_type):
    with pytest.raises(ValueError):
        _sanitize_rel_type(rel_type)

# Test the regex pattern directly
@pytest.mark.parametrize("rel_type, expected", [
    ("valid_type", True),
    ("AnotherValidType123", True),
    ("_underscore", True),
    ("", False),
    (None, False),
    (" ", False),
    ("@invalid", False),
    ("invalid-type!", False),
    ("123start", False)
])
def test_safe_identifier_pattern(rel_type, expected):
    assert bool(_SAFE_IDENTIFIER.match(rel_type)) == expected