import pytest

def health():
    if not sandbox:
        return {"status": "unhealthy", "error": "No Docker Connection"}
    return {"status": "healthy"}

@pytest.fixture
def mock_sandbox(mocker):
    mocker.patch('sandbox_service.main.sandbox', True)

def test_health_happy_path(mock_sandbox):
    assert health() == {"status": "healthy"}

def test_health_no_docker_connection():
    with pytest.raises(ValueError) as e:
        health()
    assert str(e.value) == "No Docker Connection"