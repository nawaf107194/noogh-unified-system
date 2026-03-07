import pytest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import time

# Mocking the logger to capture log messages
class LoggerMock:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)

    def warning(self, message):
        self.messages.append(message)

    def critical(self, message):
        self.messages.append(message)

# Mocking subprocess.run
def mock_subprocess_run(*args, **kwargs):
    if "--version" in args[0]:
        return MagicMock()
    else:
        raise subprocess.CalledProcessError(returncode=1, cmd=args[0])

@pytest.fixture
def start_services():
    logger = LoggerMock()
    original_logger = start_services.__globals__['logger']
    start_services.__globals__['logger'] = logger
    yield start_services
    start_services.__globals__['logger'] = original_logger

def test_happy_path(start_services):
    with patch('subprocess.run', side_effect=lambda *args, **kwargs: None) as mock_run:
        start_services()
        assert "2. BOOT SEQUENCE" in mock_run.call_args_list[0][1]['args']
        assert "/home/noogh/projects/noogh_unified_system/src/ops/docker/docker-compose.yml" in mock_run.call_args_list[1][1]['args']
        assert "-d" in mock_run.call_args_list[1][1]['args']
        assert "Waiting for convergence (10s)..." in start_services.__globals__['logger'].messages

def test_docker_compose_not_found(start_services):
    with patch('subprocess.run', side_effect=Exception()):
        start_services()
        assert "Docker Compose not found" in start_services.__globals__['logger'].messages
        assert "services are managed externally or manual start." in start_services.__globals__['logger'].messages

def test_subprocess_error(start_services):
    with patch('subprocess.run', side_effect=mock_subprocess_run) as mock_run:
        with pytest.raises(SystemExit) as exc_info:
            start_services()
        assert exc_info.value.code == 1
        assert "❌ Failed to start services" in start_services.__globals__['logger'].messages

def test_async_behavior_not_applicable(start_services):
    # Since the function does not contain async behavior, this test is irrelevant.
    pass