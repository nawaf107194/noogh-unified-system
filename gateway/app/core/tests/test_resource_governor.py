import pytest
from unittest.mock import patch, MagicMock
import logging

# Assuming the class where get_free_vram is defined is called ResourceGovernor
class ResourceGovernor:
    def __init__(self, device_type):
        self.device_type = device_type

    def get_free_vram(self) -> int:
        """Get currently free VRAM on the device."""
        from logging import getLogger

        logger = getLogger(__name__)

        if not isinstance(self.device_type, str):
            raise TypeError("device_type must be a string")

        if self.device_type == "cuda" and TORCH_AVAILABLE:
            try:
                # Clear cache to get accurate reading
                torch.cuda.empty_cache()
                free, total = torch.cuda.mem_get_info()
                logger.debug(f"Free VRAM: {free}, Total VRAM: {total}")
                return free
            except Exception as e:
                logger.error(f"Error retrieving VRAM info: {e}")
                return 0
        else:
            logger.warning("Device type is not 'cuda' or PyTorch is not available")
            return 0  # Fallback for CPU

# Mocking the global variable and the torch module
TORCH_AVAILABLE = True
torch = MagicMock()

@pytest.fixture
def resource_governor_cuda():
    return ResourceGovernor(device_type="cuda")

@pytest.fixture
def resource_governor_cpu():
    return ResourceGovernor(device_type="cpu")

@pytest.fixture
def resource_governor_invalid():
    return ResourceGovernor(device_type=123)

@pytest.mark.parametrize("device_type", ["cuda", "cpu"])
def test_get_free_vram_happy_path(resource_governor_cuda, caplog):
    with patch('torch.cuda.mem_get_info', return_value=(512, 1024)):
        assert resource_governor_cuda.get_free_vram() == 512
    assert "Free VRAM: 512, Total VRAM: 1024" in caplog.text

def test_get_free_vram_non_cuda(resource_governor_cpu, caplog):
    assert resource_governor_cpu.get_free_vram() == 0
    assert "Device type is not 'cuda' or PyTorch is not available" in caplog.text

def test_get_free_vram_invalid_device_type(resource_governor_invalid):
    with pytest.raises(TypeError, match="device_type must be a string"):
        resource_governor_invalid.get_free_vram()

def test_get_free_vram_torch_error(resource_governor_cuda, caplog):
    with patch('torch.cuda.mem_get_info', side_effect=ValueError("Mocked error")):
        assert resource_governor_cuda.get_free_vram() == 0
    assert "Error retrieving VRAM info: Mocked error" in caplog.text

def test_get_free_vram_torch_not_available(resource_governor_cuda, caplog):
    global TORCH_AVAILABLE
    TORCH_AVAILABLE = False
    assert resource_governor_cuda.get_free_vram() == 0
    assert "Device type is not 'cuda' or PyTorch is not available" in caplog.text