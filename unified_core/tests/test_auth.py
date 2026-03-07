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
        "NOOGH_ADMIN_TOKEN": "admin_token",
        "NOOGH_SERVICE_TOKEN": "service_token",
        "NOOGH_READONLY_TOKEN": "readonly_token",
        "NOOGH_INTERNAL_TOKEN": "internal_token"
    }
    expected = {
        "admin_token": {"*"},
        "service_token": {"tools:use", "http:request", "fs:read", "fs:write", "memory:rw", "exec"},
        "readonly_token": {"read:status", "read:metrics"},
        "internal_token": {"*"}
    }
    assert _build_token_scope_map(secrets) == expected

def test_build_token_scope_map_empty_secrets():
    secrets = {}
    expected = {}
    assert _build_token_scope_map(secrets) == expected

def test_build_token_scope_map_none_values():
    secrets = {
        "NOOGH_ADMIN_TOKEN": None,
        "NOOGH_SERVICE_TOKEN": None,
        "NOOGH_READONLY_TOKEN": None,
        "NOOGH_INTERNAL_TOKEN": None
    }
    expected = {}
    assert _build_token_scope_map(secrets) == expected

def test_build_token_scope_map_empty_strings():
    secrets = {
        "NOOGH_ADMIN_TOKEN": "",
        "NOOGH_SERVICE_TOKEN": "",
        "NOOGH_READONLY_TOKEN": "",
        "NOOGH_INTERNAL_TOKEN": ""
    }
    expected = {}
    assert _build_token_scope_map(secrets) == expected

def test_build_token_scope_map_mixed_values():
    secrets = {
        "NOOGH_ADMIN_TOKEN": "admin_token",
        "NOOGH_SERVICE_TOKEN": None,
        "NOOGH_READONLY_TOKEN": "",
        "NOOGH_INTERNAL_TOKEN": "internal_token"
    }
    expected = {
        "admin_token": {"*"},
        "internal_token": {"*"}
    }
    assert _build_token_scope_map(secrets) == expected