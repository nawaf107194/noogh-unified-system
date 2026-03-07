import pytest
from sandbox_service.app.core.sandbox_impl import SandboxImpl, docker

@pytest.fixture
def mock_docker_client(mocker):
    return mocker.patch('docker.from_env', return_value='mock_client')

def test_init_happy_path(mock_docker_client):
    # Arrange
    image = "python:3.12-slim"
    cpu_quota = 50000
    mem_limit = "128m"

    # Act
    sandbox = SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert sandbox.image == image
    assert sandbox.client == 'mock_client'
    assert sandbox.cpu_quota == cpu_quota
    assert sandbox.mem_limit == mem_limit
    assert sandbox.workdir == "/tmp"

def test_init_edge_case_empty_image(mock_docker_client):
    # Arrange
    image = ""
    cpu_quota = 50000
    mem_limit = "128m"

    # Act
    with pytest.raises(ValueError) as exc_info:
        SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert str(exc_info.value) == "Image cannot be empty"

def test_init_edge_case_none_image(mock_docker_client):
    # Arrange
    image = None
    cpu_quota = 50000
    mem_limit = "128m"

    # Act
    with pytest.raises(ValueError) as exc_info:
        SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert str(exc_info.value) == "Image cannot be None"

def test_init_edge_case_invalid_cpu_quota(mock_docker_client):
    # Arrange
    image = "python:3.12-slim"
    cpu_quota = -1
    mem_limit = "128m"

    # Act
    with pytest.raises(ValueError) as exc_info:
        SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert str(exc_info.value) == "CPU quota must be a non-negative integer"

def test_init_edge_case_invalid_mem_limit(mock_docker_client):
    # Arrange
    image = "python:3.12-slim"
    cpu_quota = 50000
    mem_limit = ""

    # Act
    with pytest.raises(ValueError) as exc_info:
        SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert str(exc_info.value) == "Memory limit cannot be empty"

def test_init_edge_case_none_mem_limit(mock_docker_client):
    # Arrange
    image = "python:3.12-slim"
    cpu_quota = 50000
    mem_limit = None

    # Act
    with pytest.raises(ValueError) as exc_info:
        SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert str(exc_info.value) == "Memory limit cannot be None"

def test_init_edge_case_boundary_cpu_quota(mock_docker_client):
    # Arrange
    image = "python:3.12-slim"
    cpu_quota = 0
    mem_limit = "128m"

    # Act
    sandbox = SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert sandbox.cpu_quota == cpu_quota

def test_init_edge_case_boundary_mem_limit(mock_docker_client):
    # Arrange
    image = "python:3.12-slim"
    cpu_quota = 50000
    mem_limit = "64m"

    # Act
    sandbox = SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert sandbox.mem_limit == mem_limit

def test_init_async_behavior(mocker):
    # Arrange
    image = "python:3.12-slim"
    cpu_quota = 50000
    mem_limit = "128m"

    # Mock the docker client methods to simulate async behavior
    mock_docker_client.containers.run.return_value = None
    mock_docker_client.images.pull.return_value = None

    # Act
    sandbox = SandboxImpl(image, cpu_quota, mem_limit)

    # Asserts
    assert sandbox.image == image
    assert sandbox.client == 'mock_client'
    assert sandbox.cpu_quota == cpu_quota
    assert sandbox.mem_limit == mem_limit
    assert sandbox.workdir == "/tmp"