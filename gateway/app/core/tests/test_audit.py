import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from gateway.app.core.audit import AuditLogger

@pytest.fixture
def mock_path():
    with patch('pathlib.Path', autospec=True) as MockPath:
        yield MockPath

def test_happy_path(mock_path):
    # Arrange
    mock_path_instance = mock_path.return_value
    mock_path_instance.mkdir.return_value = None
    mock_path_instance.__truediv__.return_value = mock_path_instance
    
    # Act
    audit_logger = AuditLogger("/valid/data/dir")
    
    # Assert
    assert audit_logger.audit_dir == Path("/valid/data/dir/.noogh_audit")
    assert audit_logger.log_file == Path("/valid/data/dir/.noogh_audit/audit.jsonl")

def test_empty_string_input():
    with pytest.raises(ValueError, match="data_dir is required for AuditLogger"):
        AuditLogger("")

def test_none_input():
    with pytest.raises(ValueError, match="data_dir is required for AuditLogger"):
        AuditLogger(None)

def test_invalid_input():
    with pytest.raises(ValueError, match="data_dir is required for AuditLogger"):
        AuditLogger(123)

def test_directory_creation_error(mock_path):
    # Arrange
    mock_path_instance = mock_path.return_value
    mock_path_instance.mkdir.side_effect = OSError("Mocked OS error")
    
    # Act & Assert
    with pytest.raises(OSError, match="Mocked OS error"):
        AuditLogger("/mock/failing/path")