import pytest
from subprocess import TimeoutExpired
from deep_system_scanner import _run

def test_run_valid_command_str():
    """Test running a valid command as a string"""
    result = _run("echo 'test'")
    assert result == "test"

def test_run_valid_command_list():
    """Test running a valid command as a list"""
    result = _run(["echo", "test"])
    assert result == "test"

def test_run_empty_command():
    """Test running an empty command string"""
    result = _run("")
    assert result == ""

def test_run_none_command():
    """Test running with None command"""
    result = _run(None)
    assert result == ""

def test_run_invalid_command():
    """Test running an invalid/non-existent command"""
    result = _run("invalidcommand")
    assert result == ""

def test_run_timeout():
    """Test timeout functionality by sleeping longer than timeout"""
    result = _run("sleep 10", timeout=1)
    assert result == ""