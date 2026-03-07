import pytest

from unified_core.orchestration.resource_manager import get_resource_manager, ResourceManager

@pytest.fixture(autouse=True)
def reset_resource_manager():
    global _resource_manager
    _resource_manager = None
    yield
    _resource_manager = None

def test_happy_path():
    """Test the normal behavior of the function"""
    rm1 = get_resource_manager()
    assert isinstance(rm1, ResourceManager)

    # Get it again to check if it's the same instance
    rm2 = get_resource_manager()
    assert rm1 is rm2

def test_edge_cases():
    """Test edge cases that should not be applicable here"""
    with pytest.raises(NotImplementedError):
        get_resource_manager("empty")

    with pytest.raises(NotImplementedError):
        get_resource_manager(None)

    with pytest.raises(NotImplementedError):
        get_resource_manager([])

def test_error_cases():
    """There are no explicit errors in the function, so these tests are not applicable"""
    pass

@pytest.mark.asyncio
async def test_async_behavior():
    """Test async behavior if applicable"""
    rm1 = await get_resource_manager()
    assert isinstance(rm1, ResourceManager)

    # Get it again to check if it's the same instance
    rm2 = await get_resource_manager()
    assert rm1 is rm2