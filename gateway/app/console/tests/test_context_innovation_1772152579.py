import pytest
import torch

TORCH_AVAILABLE = True

def get_gpu_context() -> dict:
    """Get GPU stats using torch only (no subprocess)"""
    if TORCH_AVAILABLE:
        try:
            free, total = torch.cuda.mem_get_info(0)
            util = 100 * (1 - free / total)
            return {"gpu_vram_gb": round(total / (1024**3), 2), "gpu_util": round(util, 1)}
        except Exception:
            pass
    return {"gpu_vram_gb": 0, "gpu_util": 0}

def test_get_gpu_context_happy_path():
    # Mock torch.cuda.mem_get_info to simulate a GPU with some VRAM and utilization
    with pytest.mock.patch("torch.cuda.mem_get_info") as mock_mem_get_info:
        mock_mem_get_info.return_value = (1024**3 * 6, 1024**3 * 8)  # 6 GB free, 8 GB total
        result = get_gpu_context()
    assert result == {"gpu_vram_gb": 8.0, "gpu_util": 25.0}

def test_get_gpu_context_no_gpu():
    global TORCH_AVAILABLE
    TORCH_AVAILABLE = False
    result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0, "gpu_util": 0}
    TORCH_AVAILABLE = True

def test_get_gpu_context_error_path():
    # Mock torch.cuda.mem_get_info to simulate an error condition
    with pytest.mock.patch("torch.cuda.mem_get_info", side_effect=Exception):
        result = get_gpu_context()
    assert result == {"gpu_vram_gb": 0, "gpu_util": 0}

def test_get_gpu_context_empty_input():
    # This function does not accept any parameters, so there is no need to test empty input
    pass

def test_get_gpu_context_none_input():
    # This function does not accept any parameters, so there is no need to test None input
    pass

def test_get_gpu_context_boundaries():
    # The function does not have specific boundary conditions to test
    pass