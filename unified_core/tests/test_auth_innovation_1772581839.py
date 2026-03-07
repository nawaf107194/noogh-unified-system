import pytest
from unified_core.auth import get_dashboard_auth, AuthContext

def test_get_dashboard_auth_happy_path():
    """Test happy path - normal function call"""
    result = get_dashboard_auth()
    assert isinstance(result, AuthContext)
    assert result == DASHBOARD_AUTH