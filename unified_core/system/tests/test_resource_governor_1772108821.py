import pytest
import psutil

class MockedResourceGovernor:
    def __init__(self, cpu_threshold=50, gpu_threshold=30):
        self.cpu_threshold = cpu_threshold
        self.gpu_threshold = gpu_threshold
    
    def get_gpu_usage(self):
        return 25  # Simulated GPU usage

def test_check_resources_happy_path():
    resource_governor = MockedResourceGovernor()
    assert resource_governor.check_resources() == True

def test_check_resources_cpu_over_limit():
    resource_governor = MockedResourceGovernor(cpu_threshold=40)
    assert resource_governor.check_resources() == False

def test_check_resources_gpu_over_limit():
    resource_governor = MockedResourceGovernor(gpu_threshold=25)
    assert resource_governor.check_resources() == False

def test_check_resources_cpu_and_gpu_over_limits():
    resource_governor = MockedResourceGovernor(cpu_threshold=40, gpu_threshold=15)
    assert resource_governor.check_resources() == False

def test_check_resources_negative_cpu_threshold():
    with pytest.raises(ValueError):
        MockedResourceGovernor(cpu_threshold=-1)

def test_check_resources_negative_gpu_threshold():
    with pytest.raises(ValueError):
        MockedResourceGovernor(gpu_threshold=-1)

def test_check_resources_non_numeric_cpu_threshold():
    with pytest.raises(TypeError):
        MockedResourceGovernor(cpu_threshold="50")

def test_check_resources_non_numeric_gpu_threshold():
    with pytest.raises(TypeError):
        MockedResourceGovernor(gpu_threshold="30")