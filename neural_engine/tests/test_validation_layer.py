import pytest

from neural_engine.validation_layer import check_file_operation_safety, SafetyChecker

def test_check_file_operation_safety_happy_path():
    operation = "write"
    path = "/home/user/documents/file.txt"
    content = "example content"

    is_safe, issues = check_file_operation_safety(operation, path, content)
    assert is_safe is True
    assert not issues

def test_check_file_operation_safety_edge_case_empty_path():
    operation = "read"
    path = ""
    content = None

    is_safe, issues = check_file_operation_safety(operation, path, content)
    assert is_safe is False
    assert issues == ["Operation on sensitive path:"]

def test_check_file_operation_safety_edge_case_none_path():
    operation = "write"
    path = None
    content = "example content"

    is_safe, issues = check_file_operation_safety(operation, path, content)
    assert is_safe is False
    assert issues == ["Operation on sensitive path:"]

def test_check_file_operation_safety_edge_case_boundary_path():
    operation = "delete"
    path = "/"
    content = None

    is_safe, issues = check_file_operation_safety(operation, path, content)
    assert is_safe is False
    assert issues == ["Cannot delete critical path: /"]

def test_check_file_operation_safety_error_case_invalid_operation():
    operation = "unknown"
    path = "/home/user/documents/file.txt"
    content = None

    is_safe, issues = check_file_operation_safety(operation, path, content)
    assert is_safe is True
    assert not issues