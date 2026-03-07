import pytest
from unittest.mock import patch, MagicMock
import threading
import time

from unified_core.dreamer import Dreamer

class TestDreamer:
    @pytest.fixture
    def dreamer(self):
        return Dreamer(interval_seconds=60.0)

    def test_happy_path(self, dreamer):
        assert dreamer._interval == 60.0
        assert isinstance(dreamer._stop_event, threading.Event)
        assert dreamer._thread is None
        assert not dreamer._running
        assert dreamer._gravity_well is None
        assert dreamer._cycle_count == 0

    def test_edge_case_none_interval(self):
        with pytest.raises(TypeError) as exc_info:
            Dreamer(interval_seconds=None)
        assert "interval_seconds must be a float" in str(exc_info.value)

    def test_edge_case_negative_interval(self):
        with pytest.raises(ValueError) as exc_info:
            Dreamer(interval_seconds=-10.0)
        assert "interval_seconds must be non-negative" in str(exc_info.value)

    def test_error_case_invalid_type_interval(self):
        with pytest.raises(TypeError) as exc_info:
            Dreamer(interval_seconds="60.0")
        assert "interval_seconds must be a float" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_behavior(self, dreamer):
        with patch.object(dreamer, '_run') as mock_run:
            dreamer.start()
            await asyncio.sleep(0.1)
            dreamer.stop()
            assert mock_run.called_once