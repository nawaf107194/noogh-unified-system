import pytest
from threading import Lock
from unified_core.system.resource_governor import ResourceGovernor

def test_init_happy_path():
    rg = ResourceGovernor()
    assert rg.max_cpu_usage == 0.85
    assert rg.max_gpu_memory == 0.75
    assert isinstance(rg.cpu_lock, Lock)
    assert isinstance(rg.gpu_lock, Lock)

def test_init_edge_cases_empty_values():
    rg = ResourceGovernor(max_cpu_usage=None, max_gpu_memory=None)
    assert rg.max_cpu_usage is None
    assert rg.max_gpu_memory is None

def test_init_edge_cases_boundary_values():
    rg = ResourceGovernor(max_cpu_usage=0.85, max_gpu_memory=0.75)
    assert rg.max_cpu_usage == 0.85
    assert rg.max_gpu_memory == 0.75

async def test_async_behavior():
    # Since the __init__ method does not perform any async operations,
    # this test is more about ensuring it can be called asynchronously.
    import asyncio
    
    async def create_resource_governor():
        return ResourceGovernor()
    
    loop = asyncio.get_event_loop()
    rg = await loop.run_in_executor(None, create_resource_governor)
    assert isinstance(rg, ResourceGovernor)

def test_init_error_cases_invalid_cpu_usage():
    with pytest.raises(ValueError):
        ResourceGovernor(max_cpu_usage=1.0)

def test_init_error_cases_invalid_gpu_memory():
    with pytest.raises(ValueError):
        ResourceGovernor(max_gpu_memory=1.5)