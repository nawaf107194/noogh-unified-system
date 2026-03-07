import pytest
from unittest.mock import patch, mock_open
import torch

from gateway.app.console.context import get_gpu_context

# Mocking torch.cuda.mem_get_info for testing different scenarios
@patch('torch.cuda.mem_get_info')
def test_get_gpu_context_happy_path(mock_mem_get_info):
    # Happy path: Normal inputs
    total_memory = 8192 * (1024**3)  # 8GB in bytes
    free_memory = 4096 * (1024**3)   # 4GB in bytes
    mock_mem_get_info.return_value = (free_memory, total_memory)
    
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 8.00, "gpu_util": 50.0}

@patch('torch.cuda.mem_get_info')
def test_get_gpu_context_zero_memory(mock_mem_get_info):
    # Edge case: Total memory is zero
    mock_mem_get_info.return_value = (0, 0)
    
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0.00, "gpu_util": 0.0}

@patch('torch.cuda.mem_get_info')
def test_get_gpu_context_negative_memory(mock_mem_get_info):
    # Edge case: Negative memory values
    mock_mem_get_info.return_value = (-1 * (1024**3), -1 * (1024**3))
    
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0.00, "gpu_util": 0.0}

@patch('torch.cuda.mem_get_info')
def test_get_gpu_context_no_torch_available(mock_mem_get_info):
    # Edge case: torch is not available
    global TORCH_AVAILABLE
    TORCH_AVAILABLE = False
    
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0.00, "gpu_util": 0.0}

@patch('torch.cuda.mem_get_info')
def test_get_gpu_context_exception(mock_mem_get_info):
    # Error case: Exception raised by torch
    mock_mem_get_info.side_effect = Exception("Mocked exception")
    
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0.00, "gpu_util": 0.0}