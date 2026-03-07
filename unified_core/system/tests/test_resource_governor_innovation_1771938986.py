import pytest
from unittest.mock import patch, Mock
import psutil

class MockResourceGovernor:
    def __init__(self):
        self.cpu_lock = Mock()
        self.gpu_lock = Mock()
        self.max_cpu_usage = 50.0
        self.max_gpu_memory = 1024

def test_check_and_throttle_happy_path():
    resource_governor = MockResourceGovernor()
    with patch.object(psutil, 'cpu_percent', return_value=40):
        with patch.object(resource_governor, '_get_gpu_memory_usage', return_value=512):
            resource_governor.check_and_throttle()
            assert not resource_governor.cpu_lock.acquire.called
            assert not resource_governor.gpu_lock.acquire.called

def test_check_and_throttle_cpu_exceeded():
    resource_governor = MockResourceGovernor()
    with patch.object(psutil, 'cpu_percent', return_value=60):
        with patch.object(resource_governor, '_get_gpu_memory_usage', return_value=512):
            resource_governor.check_and_throttle()
            assert resource_governor.cpu_lock.acquire.called
            assert not resource_governor.gpu_lock.acquire.called

def test_check_and_throttle_gpu_exceeded():
    resource_governor = MockResourceGovernor()
    with patch.object(psutil, 'cpu_percent', return_value=40):
        with patch.object(resource_governor, '_get_gpu_memory_usage', return_value=1200):
            resource_governor.check_and_throttle()
            assert not resource_governor.cpu_lock.acquire.called
            assert resource_governor.gpu_lock.acquire.called

def test_check_and_throttle_cpu_gpu_both_exceeded():
    resource_governor = MockResourceGovernor()
    with patch.object(psutil, 'cpu_percent', return_value=60):
        with patch.object(resource_governor, '_get_gpu_memory_usage', return_value=1200):
            resource_governor.check_and_throttle()
            assert resource_governor.cpu_lock.acquire.called
            assert resource_governor.gpu_lock.acquire.called

def test_check_and_throttle_cpu_boundary():
    resource_governor = MockResourceGovernor()
    with patch.object(psutil, 'cpu_percent', return_value=50):
        with patch.object(resource_governor, '_get_gpu_memory_usage', return_value=512):
            resource_governor.check_and_throttle()
            assert not resource_governor.cpu_lock.acquire.called
            assert not resource_governor.gpu_lock.acquire.called

def test_check_and_throttle_gpu_boundary():
    resource_governor = MockResourceGovernor()
    with patch.object(psutil, 'cpu_percent', return_value=40):
        with patch.object(resource_governor, '_get_gpu_memory_usage', return_value=1024):
            resource_governor.check_and_throttle()
            assert not resource_governor.cpu_lock.acquire.called
            assert not resource_governor.gpu_lock.acquire.called

def test_check_and_throttle_cpu_none():
    with pytest.raises(TypeError):
        MockResourceGovernor().max_cpu_usage = None
        with patch.object(psutil, 'cpu_percent', return_value=None):
            resource_governor.check_and_throttle()

def test_check_and_throttle_gpu_none():
    with pytest.raises(TypeError):
        MockResourceGovernor().max_gpu_memory = None
        with patch.object(resource_governor, '_get_gpu_memory_usage', return_value=None):
            resource_governor.check_and_throttle()