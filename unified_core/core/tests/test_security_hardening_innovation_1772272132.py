import pytest
from unittest.mock import patch, MagicMock
from unified_core.core.security_hardening import SecurityHardening

def test_scan_happy_path():
    hardening = SecurityHardening(['path/to/file1', 'path/to/file2'])
    
    with patch.object(hardening, '_get_hash', return_value='hash1'):
        assert hardening.scan() == ['path/to/file1']
    
    with patch.object(hardening, '_get_hash', side_effect=['hash1', 'hash2']):
        assert set(harding.scan()) == {'path/to/file1', 'path/to/file2'}

def test_scan_edge_case_empty_paths():
    hardening = SecurityHardening([])
    assert hardening.scan() == []

def test_scan_edge_case_none_paths():
    hardening = SecurityHardening(None)
    assert hardening.scan() == []

def test_scan_edge_case_boundary_single_path():
    hardening = SecurityHardening(['path/to/single/file'])
    with patch.object(hardening, '_get_hash', return_value='hash1'):
        assert hardening.scan() == ['path/to/single/file']

def test_scan_error_case_nonexistent_path():
    hardening = SecurityHardening(['nonexistent/path', 'existing/path'])
    
    with patch('os.path.exists', return_value=False), \
         patch.object(hardening, '_get_hash', return_value='hash1'):
        assert hardening.scan() == ['existing/path']

def test_scan_error_case_invalid_input():
    class InvalidInput:
        def __iter__(self):
            raise ValueError("Invalid input")
    
    with pytest.raises(ValueError):
        SecurityHardening(InvalidInput())