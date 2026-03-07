import pytest
from unified_core.evolution.sandbox import SandboxConfig, Sandbox

@pytest.fixture
def sandbox_config():
    return SandboxConfig(temp_dir='temp_test_dir')

@pytest.fixture
def sandbox(sandbox_config):
    sandbox_instance = Sandbox(config=sandbox_config)
    yield sandbox_instance
    sandbox_instance.cleanup()

def test_cleanup_happy_path(sandbox):
    # Ensure the temp directory exists before running the cleanup
    sandbox.config.temp_dir.mkdir(parents=True, exist_ok=True)
    # Add some files and directories to clean up
    (sandbox.config.temp_dir / 'file.txt').touch()
    (sandbox.config.temp_dir / 'dir1').mkdir()
    
    sandbox.cleanup()
    
    assert not sandbox.config.temp_dir.exists()

def test_cleanup_empty_directory(sandbox):
    # Ensure the temp directory exists before running the cleanup
    sandbox.config.temp_dir.mkdir(parents=True, exist_ok=True)
    
    sandbox.cleanup()
    
    assert not sandbox.config.temp_dir.exists()

def test_cleanup_none_config():
    config = None
    with pytest.raises(ValueError) as e_info:
        sandbox_instance = Sandbox(config=config)
        sandbox_instance.cleanup()
    
    assert str(e_info.value) == "Config cannot be None"

def test_cleanup_invalid_path(sandbox):
    # Set an invalid path to ensure it handles it gracefully
    sandbox.config.temp_dir = '/nonexistent/path'
    
    sandbox.cleanup()
    
    assert not sandbox.config.temp_dir.exists()