import pytest

from neural_engine.specialized_systems.gpu_controller import get_gpu_controller, GPUController

_gpu_controller = None  # Reset global variable for testing

def test_get_gpu_controller_happy_path():
    """Test happy path where the GPUController is successfully created and returned."""
    assert isinstance(get_gpu_controller(), GPUController)
    assert _gpu_controller is not None

def test_get_gpu_controller_no_global_instance():
    """Test that a new instance is created if no global instance exists."""
    global _gpu_controller
    _gpu_controller = None  # Reset global variable
    controller1 = get_gpu_controller()
    controller2 = get_gpu_controller()
    assert id(controller1) == id(controller2)
    assert isinstance(controller1, GPUController)

def test_get_gpu_controller_with_existing_instance():
    """Test that the existing instance is returned if a global instance already exists."""
    global _gpu_controller
    _gpu_controller = GPUController()  # Set an existing instance
    controller1 = get_gpu_controller()
    controller2 = get_gpu_controller()
    assert id(controller1) == id(controller2)
    assert isinstance(controller1, GPUController)

@pytest.mark.asyncio
async def test_get_gpu_controller_async():
    """Test async behavior by ensuring the function can be called in an async context."""
    global _gpu_controller
    _gpu_controller = None  # Reset global variable
    controller = await get_gpu_controller()
    assert isinstance(controller, GPUController)
    assert _gpu_controller is not None