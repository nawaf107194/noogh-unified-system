import pytest

from neural_engine.tools.internal_api_tool import get_api_caller, InternalAPICaller

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton instance before each test."""
    global _caller_instance
    _caller_instance = None

def test_get_api_caller_happy_path():
    caller1 = get_api_caller()
    caller2 = get_api_caller()
    
    assert caller1 is not None
    assert caller2 is not None
    assert caller1 is caller2  # Singleton, same instance returned
    
    assert isinstance(caller1, InternalAPICaller)

def test_get_api_caller_edge_case_none():
    global _caller_instance
    _caller_instance = None
    caller = get_api_caller()
    
    assert caller is not None
    assert isinstance(caller, InternalAPICaller)

def test_get_api_caller_edge_case_not_none():
    global _caller_instance
    _caller_instance = InternalAPICaller()
    caller = get_api_caller()
    
    assert caller is not None
    assert caller is _caller_instance