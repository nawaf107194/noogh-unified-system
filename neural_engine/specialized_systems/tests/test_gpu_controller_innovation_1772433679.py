import pytest

from neural_engine.specialized_systems.gpu_controller import get_gpu_controller, GPUController


@pytest.fixture(autouse=True)
def mock_gpu_controller():
    """Mock the global _gpu_controller for testing."""
    global _gpu_controller
    _gpu_controller = None


def test_happy_path(monkeypatch):
    gpu_controller = get_gpu_controller()
    assert isinstance(gpu_controller, GPUController)


def test_edge_case_none(monkeypatch):
    with pytest.raises(AttributeError) as exc_info:
        global _gpu_controller
        _gpu_controller = None
        get_gpu_controller()
    assert str(exc_info.value).startswith("module '__main__' has no attribute '_gpu_controller'")


def test_error_cases_invalid_input():
    # Since the function does not accept any parameters, there are no invalid inputs to test.
    pass


async def test_async_behavior(mocker):
    gpu_controller = await get_gpu_controller()
    assert isinstance(gpu_controller, GPUController)