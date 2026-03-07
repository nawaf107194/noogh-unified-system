import pytest
from unified_core.identity import SelfIdentity

@pytest.fixture
def identity():
    return SelfIdentity()

def test_introspect_happy_path(identity):
    active_goals = {
        "goal1": "compress data",
        "goal2": "optimize performance"
    }
    result = identity.introspect(active_goals)
    assert result == {
        "status": "authority_removed",
        "gaps": ["Meta-cognition delegated to WorldModel"],
        "needs_innovation": False,
        "warning": "This module has no cognitive authority"
    }

def test_introspect_empty_input(identity):
    active_goals = {}
    result = identity.introspect(active_goals)
    assert result == {
        "status": "authority_removed",
        "gaps": ["Meta-cognition delegated to WorldModel"],
        "needs_innovation": False,
        "warning": "This module has no cognitive authority"
    }

def test_introspect_none_input(identity):
    active_goals = None
    result = identity.introspect(active_goals)
    assert result == {
        "status": "authority_removed",
        "gaps": ["Meta-cognition delegated to WorldModel"],
        "needs_innovation": False,
        "warning": "This module has no cognitive authority"
    }

def test_introspect_logging(identity, caplog):
    active_goals = {"goal1": "compress data"}
    with caplog.at_level(logging.WARNING):
        identity.introspect(active_goals)
    assert "SelfIdentity.introspect() called - NO COGNITIVE AUTHORITY" in caplog.text

# No error cases as the function does not raise any exceptions