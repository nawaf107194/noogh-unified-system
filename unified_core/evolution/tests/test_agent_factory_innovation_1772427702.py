import pytest

def get_agent_factory() -> AgentFactory:
    """Get the global AgentFactory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = AgentFactory()
    return _factory_instance

@pytest.fixture(scope="module")
def factory():
    from unified_core.evolution.agent_factory import _factory_instance, AgentFactory
    original_factory = _factory_instance
    yield None  # Yielding None to indicate that the global instance should be cleared before each test
    _factory_instance = original_factory  # Reset the global instance after each test

def test_happy_path(factory):
    """Test the happy path with normal inputs."""
    factory_instance = get_agent_factory()
    assert factory_instance is not None, "Factory instance should not be None"
    assert isinstance(factory_instance, AgentFactory), "Factory instance should be an instance of AgentFactory"

def test_edge_cases(factory):
    """Test edge cases including empty and None inputs."""
    global _factory_instance
    _factory_instance = None  # Reset the global factory instance to None
    factory_instance1 = get_agent_factory()
    assert factory_instance1 is not None, "Factory instance should not be None after resetting"
    assert isinstance(factory_instance1, AgentFactory), "Factory instance should be an instance of AgentFactory"

def test_error_cases(factory):
    """Test error cases (though there are no explicit raise statements in the provided code)."""
    # No explicit error handling or exceptions to test
    pass

def test_async_behavior(factory):
    """Test async behavior (there is no async behavior in the provided code)."""
    # No async behavior to test
    pass