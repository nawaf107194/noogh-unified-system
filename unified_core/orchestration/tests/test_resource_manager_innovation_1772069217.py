import pytest
from unittest.mock import patch, MagicMock
import asyncio

from unified_core.orchestration.resource_manager import ResourceManager
import logging

# Mock logger to avoid actual log output during tests
@pytest.fixture
def mock_logger():
    with patch.object(logging, 'info', return_value=None) as mock:
        yield mock

async def test_init_happy_path(mock_logger):
    resource_manager = ResourceManager()
    assert isinstance(resource_manager._gpu_tokens, dict)
    assert resource_manager._gpu_tokens == {"none": 0, "low": 0, "medium": 0, "high": 0}
    assert isinstance(resource_manager._file_locks, dict)
    assert resource_manager._file_locks == {}
    assert isinstance(resource_manager._tool_last_used, dict)
    assert resource_manager._tool_last_used == {}
    assert resource_manager._tool_min_interval_ms == 1000
    assert isinstance(resource_manager._active_tasks, dict)
    assert resource_manager._active_tasks == {}
    assert isinstance(resource_manager._lock, asyncio.Lock)
    mock_logger.assert_called_once_with("✅ ResourceManager initialized")

async def test_init_edge_case_empty_input(mock_logger):
    with pytest.raises(Exception) as exc_info:
        resource_manager = ResourceManager(None)
    assert "Invalid input" in str(exc_info.value)

async def test_init_async_behavior():
    # This test is not applicable since the __init__ method does not have any
    # asynchronous behavior.
    pass