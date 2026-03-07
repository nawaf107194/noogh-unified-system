import pytest

from gateway.app.console.routes import _role_from_scopes


def test_role_from_scopes_happy_path():
    assert _role_from_scopes({"read", "write"}) == "observer"
    assert _role_from_scopes({"exec:command1", "exec:command2"}) == "operator"
    assert _role_from_scopes({"*"}) == "admin"


def test_role_from_scopes_edge_cases():
    assert _role_from_scopes(set()) == "observer"
    assert _role_from_scopes(None) is None  # Assuming None is a valid input and returns None
    assert _role_from_scopes(["read", "write"]) == "observer"  # Non-set input


def test_role_from_scopes_error_cases():
    # The function does not explicitly raise any errors, so no need to add error tests here
    pass


# Async behavior is not applicable in this synchronous function