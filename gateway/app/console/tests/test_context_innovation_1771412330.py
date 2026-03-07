import pytest
from unittest.mock import patch, MagicMock
import torch

@pytest.fixture
def mock_torch_cuda():
    with patch('torch.cuda') as mock_cuda:
        yield mock_cuda

def test_get_gpu_context_happy_path(mock_torch_cuda):
    mock_torch_cuda.is_available.return_value = True
    mock_torch_cuda.mem_get_info.return_value = (5368709120, 10737418240)  # 5GB free, 10GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 10.0, "gpu_util": 50.0}

def test_get_gpu_context_no_torch(mock_torch_cuda):
    mock_torch_cuda.is_available.return_value = False
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0, "gpu_util": 0}

def test_get_gpu_context_exception(mock_torch_cuda):
    mock_torch_cuda.is_available.return_value = True
    mock_torch_cuda.mem_get_info.side_effect = Exception("Mocked exception")
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0, "gpu_util": 0}

def test_get_gpu_context_zero_values(mock_torch_cuda):
    mock_torch_cuda.is_available.return_value = True
    mock_torch_cuda.mem_get_info.return_value = (0, 0)  # 0GB free, 0GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0, "gpu_util": 0}

def test_get_gpu_context_max_utilization(mock_torch_cuda):
    mock_torch_cuda.is_available.return_value = True
    mock_torch_cuda.mem_get_info.return_value = (1, 1024**3)  # 1B free, 1GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 1.0, "gpu_util": 100.0}

def test_get_gpu_context_min_utilization(mock_torch_cuda):
    mock_torch_cuda.is_available.return_value = True
    mock_torch_cuda.mem_get_info.return_value = (1024**3 - 1, 1024**3)  # 1GB - 1B free, 1GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 1.0, "gpu_util": 0.0}