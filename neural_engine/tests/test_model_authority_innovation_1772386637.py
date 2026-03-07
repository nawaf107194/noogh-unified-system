import pytest
from neural_engine.model_authority import ModelAuthority

def test_get_available_vram_happy_path():
    model_authority = ModelAuthority()
    available_vram = model_authority._get_available_vram()
    assert isinstance(available_vram, float)
    assert available_vram >= 0.0

@patch('torch.cuda.is_available', return_value=False)
def test_get_available_vram_no_gpu(mock_is_available):
    model_authority = ModelAuthority()
    available_vram = model_authority._get_available_vram()
    assert available_vram == 0.0
    mock_is_available.assert_called_once()

@patch('torch.cuda.is_available', return_value=True)
def test_get_available_vram_success(mock_is_available):
    with patch('torch.cuda.get_device_properties') as mock_get_device_properties:
        mock_get_device_properties.return_value.total_memory = 16 * 1024**3
        with patch('torch.cuda.memory_allocated') as mock_memory_allocated:
            mock_memory_allocated.return_value = 8 * 1024**3
            with patch('torch.cuda.memory_reserved') as mock_memory_reserved:
                mock_memory_reserved.return_value = 4 * 1024**3
                model_authority = ModelAuthority()
                available_vram = model_authority._get_available_vram()
                assert available_vram == 8.0

@patch('torch.cuda.is_available', return_value=True)
def test_get_available_vram_error(mock_is_available):
    with patch('torch.cuda.get_device_properties') as mock_get_device_properties:
        mock_get_device_properties.side_effect = Exception("Simulated error")
        model_authority = ModelAuthority()
        available_vram = model_authority._get_available_vram()
        assert available_vram == 0.0