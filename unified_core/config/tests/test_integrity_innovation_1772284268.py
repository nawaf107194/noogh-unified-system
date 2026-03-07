import pytest
from unified_core.config.integrity import initialize_directories
from pathlib import Path

def test_happy_path(monkeypatch):
    directories = [
        "/tmp/test_data_dir",
        "/tmp/test_log_dir",
        "/tmp/test_artifacts_dir",
        "/tmp/test_world_state_dir",
        "/tmp/test_backup_dir",
        "/tmp/test_scars_dir",
        "/tmp/test_protected_dir",
        "/tmp/test_consequence_dir",
        "/tmp/test_coercive_dir"
    ]
    
    def mock_path_mkdir(*args, **kwargs):
        return None
    
    monkeypatch.setattr(Path, "mkdir", mock_path_mkdir)
    
    initialize_directories()
    
    for directory in directories:
        assert Path(directory).exists()

def test_edge_cases(monkeypatch):
    directories = [
        "",  # Empty string
        None,  # None type
        "/tmp/test_dir with spaces",  # Directory with spaces
        "/tmp/test_dir\twith\tspaces",  # Directory with tabs
        "/tmp/test_dir\nwith\nnewlines",  # Directory with newlines
        "/tmp/test_dir\rwith\rreturns",  # Directory with returns
    ]
    
    def mock_path_mkdir(*args, **kwargs):
        return None
    
    monkeypatch.setattr(Path, "mkdir", mock_path_mkdir)
    
    for directory in directories:
        initialize_directories()  # This should not raise any exceptions

def test_error_cases(monkeypatch):
    directories = [
        "/tmp/test_dir with spaces",  # Directory with spaces
        "/tmp/test_dir\twith\tspaces",  # Directory with tabs
        "/tmp/test_dir\nwith\nnewlines",  # Directory with newlines
        "/tmp/test_dir\rwith\rreturns",  # Directory with returns
    ]
    
    def mock_path_mkdir(*args, **kwargs):
        raise Exception("Failed to create directory")
    
    monkeypatch.setattr(Path, "mkdir", mock_path_mkdir)
    
    for directory in directories:
        with pytest.raises(RuntimeError) as exc_info:
            initialize_directories()
        assert str(exc_info.value) == f"Failed to create directory {directory}: Failed to create directory"

# Async behavior is not applicable in this function