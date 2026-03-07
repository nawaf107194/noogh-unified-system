import pytest
from noogh.utils.security import secure_find
import os

def test_successful_search():
    search_path = "/tmp"
    name_pattern = "testfile.txt"
    max_results = 10
    timeout = 5
    
    result, output = secure_find(search_path, name_pattern, max_results, timeout)
    assert result == True
    assert isinstance(output, str)

def test_empty_search_path():
    search_path = ""
    name_pattern = "testfile.txt"
    max_results = 10
    timeout = 5
    
    result, output = secure_find(search_path, name_pattern, max_results, timeout)
    assert result == False
    assert output == "Error: Directory not found:"

def test_none_search_path():
    search_path = None
    name_pattern = "testfile.txt"
    max_results = 10
    timeout = 5
    
    result, output = secure_find(search_path, name_pattern, max_results, timeout)
    assert result == False
    assert output == "Error: Directory not found:"

def test_boundary_max_results():
    search_path = "/tmp"
    name_pattern = "*"
    max_results = 0
    timeout = 5
    
    result, output = secure_find(search_path, name_pattern, max_results, timeout)
    assert result == False
    assert output == "Error: Directory not found:"

def test_boundary_timeout():
    search_path = "/tmp"
    name_pattern = "*"
    max_results = 10
    timeout = -1
    
    result, output = secure_find(search_path, name_pattern, max_results, timeout)
    assert result == False
    assert output == "Error: Directory not found:"

def test_invalid_filename():
    search_path = "/tmp"
    name_pattern = ".."
    max_results = 10
    timeout = 5
    
    result, output = secure_find(search_path, name_pattern, max_results, timeout)
    assert result == False
    assert output == "Security Error: Invalid filename - path traversal detected"

def test_non_existent_directory():
    search_path = "/nonexistent"
    name_pattern = "*"
    max_results = 10
    timeout = 5
    
    result, output = secure_find(search_path, name_pattern, max_results, timeout)
    assert result == False
    assert output == "Error: Directory not found:"

def test_timeout():
    search_path = "/tmp"
    name_pattern = "*"
    max_results = 10
    timeout = 0.01
    
    result, output = secure_find(search_path, name_pattern, max_results, timeout)
    assert result == False
    assert output == "Timeout: Find command took too long"

def test_subprocess_failure():
    search_path = "/tmp"
    name_pattern = "*"
    max_results = 10
    timeout = 5
    
    # Mock subprocess.run to simulate a failure
    with patch('noogh.utils.security.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "find", stderr="error message")
        result, output = secure_find(search_path, name_pattern, max_results, timeout)
    
    assert result == False
    assert output.startswith("Find error: error mess")

def test_shell_false():
    search_path = "/tmp"
    name_pattern = "*"
    max_results = 10
    timeout = 5
    
    # Check that shell=False is passed to subprocess.run
    with patch('noogh.utils.security.subprocess.run') as mock_run:
        secure_find(search_path, name_pattern, max_results, timeout)
        mock_run.assert_called_once_with(
            ["find", search_path, "-name", name_pattern, "-type", "f"],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )