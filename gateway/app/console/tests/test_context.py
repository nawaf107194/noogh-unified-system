import pytest
from unittest.mock import patch, MagicMock
import torch

@pytest.fixture
def mock_torch_cuda():
    with patch('torch.cuda', new_callable=MagicMock) as mock_cuda:
        yield mock_cuda

def test_get_gpu_context_happy_path(mock_torch_cuda):
    mock_torch_cuda.mem_get_info.return_value = (5368709120, 10737418240)  # 5GB free, 10GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 10.0, "gpu_util": 50.0}

def test_get_gpu_context_no_torch_available():
    with patch('context.TORCH_AVAILABLE', False):
        result = get_gpu_context()
        assert result == {"gpu_vram_gb": 0, "gpu_util": 0}

def test_get_gpu_context_exception_raised(mock_torch_cuda):
    mock_torch_cuda.mem_get_info.side_effect = RuntimeError("CUDA error")
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0, "gpu_util": 0}

def test_get_gpu_context_zero_values(mock_torch_cuda):
    mock_torch_cuda.mem_get_info.return_value = (0, 0)  # 0GB free, 0GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0.0, "gpu_util": 0.0}

def test_get_gpu_context_all_free(mock_torch_cuda):
    mock_torch_cuda.mem_get_info.return_value = (10737418240, 10737418240)  # 10GB free, 10GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 10.0, "gpu_util": 0.0}

def test_get_gpu_context_all_used(mock_torch_cuda):
    mock_torch_cuda.mem_get_info.return_value = (0, 10737418240)  # 0GB free, 10GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 10.0, "gpu_util": 100.0}

def test_get_gpu_context_rounding(mock_torch_cuda):
    mock_torch_cuda.mem_get_info.return_value = (536870912, 1073741824)  # 0.5GB free, 1GB total
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 1.0, "gpu_util": 50.0}