import pytest

def _build_token_scope_map(secrets: Dict[str, str]) -> Dict[str, Set[str]]:
    """Build token to scopes mapping from secrets."""
    admin = secrets.get("NOOGH_ADMIN_TOKEN", "").strip()
    service = secrets.get("NOOGH_SERVICE_TOKEN", "").strip()
    readonly = secrets.get("NOOGH_READONLY_TOKEN", "").strip()
    internal = secrets.get("NOOGH_INTERNAL_TOKEN", "").strip()

    mapping = {}
    if admin:
        mapping[admin] = {"*"}
    if internal:
        mapping[internal] = {"*"}
    if service:
        mapping[service] = {"tools:use", "http:request", "fs:read", "fs:write", "memory:rw", "exec"}
    if readonly:
        mapping[readonly] = {"read:status", "read:metrics"}
    return mapping

def test_build_token_scope_map_happy_path():
    secrets = {
        "NOOGH_ADMIN_TOKEN": "admin",
        "NOOGH_SERVICE_TOKEN": "service",
        "NOOGH_READONLY_TOKEN": "readonly",
        "NOOGH_INTERNAL_TOKEN": "internal"
    }
    expected_output = {
        "admin": {"*"},
        "service": {"tools:use", "http:request", "fs:read", "fs:write", "memory:rw", "exec"},
        "readonly": {"read:status", "read:metrics"},
        "internal": {"*"}
    }
    assert _build_token_scope_map(secrets) == expected_output

def test_build_token_scope_map_edge_case_empty_values():
    secrets = {
        "NOOGH_ADMIN_TOKEN": "",
        "NOOGH_SERVICE_TOKEN": "",
        "NOOGH_READONLY_TOKEN": "",
        "NOOGH_INTERNAL_TOKEN": ""
    }
    expected_output = {}
    assert _build_token_scope_map(secrets) == expected_output

def test_build_token_scope_map_edge_case_none_values():
    secrets = {
        "NOOGH_ADMIN_TOKEN": None,
        "NOOGH_SERVICE_TOKEN": None,
        "NOOGH_READONLY_TOKEN": None,
        "NOOGH_INTERNAL_TOKEN": None
    }
    expected_output = {}
    assert _build_token_scope_map(secrets) == expected_output

def test_build_token_scope_map_edge_case_missing_keys():
    secrets = {
        "NOOGH_ADMIN_TOKEN": "",
        "NOOGH_SERVICE_TOKEN": ""
    }
    expected_output = {
        "admin": {"*"},
        "service": {"tools:use", "http:request", "fs:read", "fs:write", "memory:rw", "exec"}
    }
    assert _build_token_scope_map(secrets) == expected_output

def test_build_token_scope_map_error_case_invalid_input():
    with pytest.raises(TypeError):
        _build_token_scope_map("not a dictionary")