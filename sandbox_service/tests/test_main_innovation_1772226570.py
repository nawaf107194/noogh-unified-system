import pytest

from sandbox_service.main import health, sandbox

# Mocking the sandbox variable for testing purposes
sandbox = True  # Normally this would be set by your application context

def test_health_happy_path():
    global sandbox
    sandbox = True
    assert health() == {"status": "healthy"}

def test_health_unhealthy_no_docker_connection():
    global sandbox
    sandbox = False
    assert health() == {"status": "unhealthy", "error": "No Docker Connection"}