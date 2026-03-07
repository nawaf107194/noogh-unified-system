import pytest

from gateway.app.core.docker_sandbox import DockerSandbox

def test_init_happy_path():
    sandbox = DockerSandbox()
    assert sandbox.image == "python:3.12-slim"
    assert sandbox.timeout == 10

def test_init_with_custom_image():
    custom_image = "custom-image:latest"
    sandbox = DockerSandbox(image=custom_image)
    assert sandbox.image == custom_image
    assert sandbox.timeout == 10

def test_init_with_custom_timeout():
    custom_timeout = 30
    sandbox = DockerSandbox(timeout=custom_timeout)
    assert sandbox.image == "python:3.12-slim"
    assert sandbox.timeout == custom_timeout

def test_init_with_empty_image():
    sandbox = DockerSandbox(image="")
    assert sandbox.image == "python:3.12-slim"
    assert sandbox.timeout == 10

def test_init_with_none_image():
    sandbox = DockerSandbox(image=None)
    assert sandbox.image == "python:3.12-slim"
    assert sandbox.timeout == 10

def test_init_with_negative_timeout():
    with pytest.raises(ValueError) as exc_info:
        DockerSandbox(timeout=-5)
    assert str(exc_info.value) == "Timeout must be a non-negative integer"

def test_init_with_non_integer_timeout():
    with pytest.raises(TypeError) as exc_info:
        DockerSandbox(timeout="not an int")
    assert str(exc_info.value) == "Timeout must be a non-negative integer"