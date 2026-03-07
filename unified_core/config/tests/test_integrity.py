import pytest
from pathlib import Path
from unified_core.config.integrity import initialize_directories

def test_happy_path(monkeypatch):
    """
    Test that initializes directories successfully.
    """
    # Mock the settings module to return a list of directories
    mock_settings = {
        'DATA_DIR': '/tmp/data',
        'LOG_DIR': '/tmp/logs',
        'ARTIFACTS_DIR': '/tmp/artifacts',
        'WORLD_STATE_DIR': '/tmp/world_state',
        'BACKUP_DIR': '/tmp/backup',
        'SCARS_DIR': '/tmp/scars',
        'PROTECTED_DIR': '/tmp/protected',
        'CONSEQUENCE_DIR': '/tmp/consequence',
        'COERCIVE_DIR': '/tmp/coercive'
    }
    
    monkeypatch.setattr('unified_core.config.settings', mock_settings)

    # Mock the Path.mkdir method to do nothing
    def mock_mkdir(path, parents=True, exist_ok=True):
        pass

    monkeypatch.setattr('pathlib.Path.mkdir', mock_mkdir)
    
    initialize_directories()
    
    for directory in mock_settings.values():
        assert Path(directory).exists(), f"Directory {directory} was not created"

def test_edge_cases(monkeypatch):
    """
    Test edge cases such as empty and None inputs.
    """
    # Mock the settings module to return an empty list of directories
    monkeypatch.setattr('unified_core.config.settings', {})

    initialize_directories()

    for directory in []:
        assert not Path(directory).exists(), f"Directory {directory} was created"

def test_error_cases(monkeypatch):
    """
    Test error cases such as invalid inputs.
    """
    # Mock the settings module to return an empty list of directories
    monkeypatch.setattr('unified_core.config.settings', None)

    with pytest.raises(RuntimeError) as exc_info:
        initialize_directories()
    
    assert "Failed to create directory" in str(exc_info.value)