import pytest
from threading import Lock
from unified_core.system.resource_governor import ResourceGovernor

def test_init_happy_path():
    # Test normal inputs
    rg = ResourceGovernor(max_cpu_usage=0.85, max_gpu_memory=0.75)
    assert rg.max_cpu_usage == 0.85
    assert rg.max_gpu_memory == 0.75
    assert isinstance(rg.cpu_lock, Lock)
    assert isinstance(rg.gpu_lock, Lock)

def test_init_empty_inputs():
    # Test empty inputs (should use defaults)
    rg = ResourceGovernor()
    assert rg.max_cpu_usage == 0.85
    assert rg.max_gpu_memory == 0.75
    assert isinstance(rg.cpu_lock, Lock)
    assert isinstance(rg.gpu_lock, Lock)

def test_init_none_inputs():
    # Test None inputs (should use defaults)
    rg = ResourceGovernor(max_cpu_usage=None, max_gpu_memory=None)
    assert rg.max_cpu_usage == 0.85
    assert rg.max_gpu_memory == 0.75
    assert isinstance(rg.cpu_lock, Lock)
    assert isinstance(rg.gpu_lock, Lock)

def test_init_boundary_values():
    # Test boundary values
    rg = ResourceGovernor(max_cpu_usage=1.0, max_gpu_memory=1.0)
    assert rg.max_cpu_usage == 1.0
    assert rg.max_gpu_memory == 1.0
    assert isinstance(rg.cpu_lock, Lock)
    assert isinstance(rg.gpu_lock, Lock)

def test_init_invalid_input_types():
    # Test invalid input types (should use defaults)
    rg = ResourceGovernor(max_cpu_usage="invalid", max_gpu_memory="invalid")
    assert rg.max_cpu_usage == 0.85
    assert rg.max_gpu_memory == 0.75
    assert isinstance(rg.cpu_lock, Lock)
    assert isinstance(rg.gpu_lock, Lock)

def test_init_invalid_range_values():
    # Test invalid range values (should use defaults)
    rg = ResourceGovernor(max_cpu_usage=1.5, max_gpu_memory=1.2)
    assert rg.max_cpu_usage == 0.85
    assert rg.max_gpu_memory == 0.75
    assert isinstance(rg.cpu_lock, Lock)
    assert isinstance(rg.gpu_lock, Lock)