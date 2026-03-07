import pytest
from unittest.mock import patch, MagicMock
from typing import Dict

from gateway.app.core.resource_governor import gpu_manager
from unified_core.tool_registry import UnifiedCoreToolRegistry

def test_get_gpu_info_happy_path():
    registry = UnifiedCoreToolRegistry()
    with patch.object(gpu_manager, 'get_stats', return_value={
        'free_vram_gb': 10.23,
        'total_vram_gb': 20.45,
        'utilization': 75
    }):
        result = registry._get_gpu_info()
        assert result == {
            "vram_free_gb": 10.23,
            "vram_total_gb": 20.45,
            "utilization": 75
        }

def test_get_gpu_info_error_case():
    registry = UnifiedCoreToolRegistry()
    with patch.object(gpu_manager, 'get_stats', side_effect=Exception("Simulated error")):
        result = registry._get_gpu_info()
        assert result == {
            "error": "Failed to get GPU stats: Simulated error"
        }