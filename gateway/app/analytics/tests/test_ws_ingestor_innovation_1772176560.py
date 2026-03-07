import pytest
from typing import Optional, Set
import asyncio
from unittest.mock import patch, MagicMock
import os

# Import the actual class from the module
from gateway.app.analytics.ws_ingestor import WsIngestor

class TestWsIngestor:
    @pytest.fixture
    def ws_ingestor(self):
        return WsIngestor(poll_interval=2.0)

    def test_init_happy_path(self, ws_ingestor):
        assert ws_ingestor.poll_interval == 2.0
        assert not ws_ingestor.running
        assert ws_ingestor._task is None
        assert isinstance(ws_ingestor._seen, set)
        assert ws_ingestor._seen_max == 2000
        assert ws_ingestor.neural_events_url == "http://127.0.0.1:8080/api/v1/autonomic/events"

    def test_init_empty_poll_interval(self):
        ws_ingestor = WsIngestor(poll_interval=None)
        assert ws_ingestor.poll_interval == 2.0

    def test_init_negative_poll_interval(self):
        with patch.dict(os.environ, {"NEURAL_SERVICE_URL": "http://127.0.0.1:8080"}):
            ws_ingestor = WsIngestor(poll_interval=-1)
            assert ws_ingestor.poll_interval == 2.0

    def test_init_boundary_poll_interval(self):
        with patch.dict(os.environ, {"NEURAL_SERVICE_URL": "http://127.0.0.1:8080"}):
            ws_ingestor = WsIngestor(poll_interval=0)
            assert ws_ingestor.poll_interval == 2.0

    def test_init_non_numeric_poll_interval(self):
        with patch.dict(os.environ, {"NEURAL_SERVICE_URL": "http://127.0.0.1:8080"}):
            ws_ingestor = WsIngestor(poll_interval="not a number")
            assert ws_ingestor.poll_interval == 2.0

    def test_init_with_env_var(self, monkeypatch):
        monkeypatch.setenv("NEURAL_SERVICE_URL", "http://127.0.0.1:8080")
        ws_ingestor = WsIngestor()
        assert ws_ingestor.neural_events_url == "http://127.0.0.1:8080/api/v1/autonomic/events"

    def test_init_with_no_env_var(self):
        with patch.dict(os.environ, {"NEURAL_SERVICE_URL": ""}):
            ws_ingestor = WsIngestor()
            assert ws_ingestor.neural_events_url == "http://127.0.0.1:8080/api/v1/autonomic/events"

    def test_init_with_invalid_env_var(self, monkeypatch):
        monkeypatch.setenv("NEURAL_SERVICE_URL", "invalid://url")
        ws_ingestor = WsIngestor()
        assert ws_ingestor.neural_events_url == "http://127.0.0.1:8080/api/v1/autonomic/events"