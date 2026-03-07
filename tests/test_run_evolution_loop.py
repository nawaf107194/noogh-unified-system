import pytest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

def load_neuron_func(neuron_path: Path, func_name: str):
    module_name = f"dyn_{neuron_path.stem}"
    spec = spec_from_file_location(module_name, str(neuron_path))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func_name)

# Happy path
def test_load_neuron_func_happy_path(tmp_path):
    neuron_path = tmp_path / "test_neuron.py"
    with open(neuron_path, 'w') as f:
        f.write("def my_function():\n    return 42\n")
    
    result = load_neuron_func(neuron_path, "my_function")
    assert result() == 42

# Edge cases
def test_load_neuron_func_empty_path():
    with pytest.raises(ValueError):
        load_neuron_func(Path(""), "my_function")

def test_load_neuron_func_none_path():
    with pytest.raises(ValueError):
        load_neuron_func(None, "my_function")

def test_load_neuron_func_boundary_path(tmp_path):
    neuron_path = tmp_path / "test_neuron.py"
    result = load_neuron_func(neuron_path, "nonexistent_function")
    assert result is None

# Error cases
def test_load_neuron_func_invalid_module_name(tmp_path):
    neuron_path = tmp_path / "test_neuron.py"
    with open(neuron_path, 'w') as f:
        f.write("invalid syntax")
    
    with pytest.raises(ImportError):
        load_neuron_func(neuron_path, "my_function")

def test_load_neuron_func_invalid_function_name(tmp_path):
    neuron_path = tmp_path / "test_neuron.py"
    with open(neuron_path, 'w') as f:
        f.write("def my_function():\n    return 42\n")
    
    result = load_neuron_func(neuron_path, "nonexistent_function")
    assert result is None

# Async behavior (not applicable)