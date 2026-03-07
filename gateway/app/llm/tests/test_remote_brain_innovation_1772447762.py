import os
from unittest.mock import patch, mock_open
import pytest

from gateway.app.llm.remote_brain import RemoteBrainService
from config.ports import PORTS
from settings import BASE_MODEL_NAME
import logging

# Mock the logger to avoid actual logging during tests
def mock_logger():
    with patch('logging.info') as mock_info:
        yield mock_info

def test_happy_path(monkeypatch):
    with mock_logger() as mock_log:
        monkeypatch.setenv("NEURAL_ENGINE_URL", None)
        service = RemoteBrainService()
        assert service.neural_engine_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}"
        assert service.tokenizer is None
        assert service.model == f"Remote: {BASE_MODEL_NAME}"
        mock_log.assert_called_once_with(f"Initialized RemoteBrainService pointing to http://127.0.0.1:{PORTS.NEURAL_ENGINE}")

def test_empty_neural_engine_url(monkeypatch):
    with mock_logger() as mock_log:
        monkeypatch.setenv("NEURAL_ENGINE_URL", "")
        service = RemoteBrainService()
        assert service.neural_engine_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}"
        assert service.tokenizer is None
        assert service.model == f"Remote: {BASE_MODEL_NAME}"
        mock_log.assert_called_once_with(f"Initialized RemoteBrainService pointing to http://127.0.0.1:{PORTS.NEURAL_ENGINE}")

def test_none_neural_engine_url(monkeypatch):
    with mock_logger() as mock_log:
        monkeypatch.setenv("NEURAL_ENGINE_URL", None)
        service = RemoteBrainService()
        assert service.neural_engine_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}"
        assert service.tokenizer is None
        assert service.model == f"Remote: {BASE_MODEL_NAME}"
        mock_log.assert_called_once_with(f"Initialized RemoteBrainService pointing to http://127.0.0.1:{PORTS.NEURAL_ENGINE}")

def test_invalid_neural_engine_url(monkeypatch):
    with mock_logger() as mock_log:
        monkeypatch.setenv("NEURAL_ENGINE_URL", "invalid")
        service = RemoteBrainService()
        assert service.neural_engine_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}"
        assert service.tokenizer is None
        assert service.model == f"Remote: {BASE_MODEL_NAME}"
        mock_log.assert_called_once_with(f"Initialized RemoteBrainService pointing to http://127.0.0.1:{PORTS.NEURAL_ENGINE}")