import pytest

from gateway.app.api.system_routes import get_gpu_stats

def test_get_gpu_stats_happy_path():
    # Mock torch.cuda.is_available and other necessary functions to simulate a GPU being available
    with patch('torch.cuda.is_available', return_value=True):
        with patch('torch.cuda.get_device_properties') as mock_get_device_properties:
            mock_get_device_properties.return_value = Mock(total_memory=16 * (1024**3))
        
        with patch('torch.cuda.memory_allocated') as mock_memory_allocated:
            mock_memory_allocated.return_value = 8 * (1024**3)
        
        with patch('torch.cuda.mem_get_info') as mock_mem_get_info:
            mock_mem_get_info.return_value = (8 * (1024**3), 16 * (1024**3))
        
        result = get_gpu_stats()
    
    assert result == {
        "total_vram_gb": 16.0,
        "free_vram_gb": 8.0,
        "utilization": 0.5
    }

def test_get_gpu_stats_no_gpu():
    with patch('torch.cuda.is_available', return_value=False):
        result = get_gpu_stats()
    
    assert result == {
        "total_vram_gb": 0,
        "free_vram_gb": 0,
        "utilization": 0
    }

def test_get_gpu_stats_import_error():
    # Mock the import to simulate an ImportError
    with patch.dict('sys.modules', {'torch': None}):
        result = get_gpu_stats()
    
    assert result == {
        "total_vram_gb": 0,
        "free_vram_gb": 0,
        "utilization": 0
    }