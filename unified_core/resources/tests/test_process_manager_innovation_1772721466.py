import pytest
from unittest.mock import Mock
from ...process_manager import ProcessManager

def test_protect_adds_pid():
    manager = ProcessManager()
    pid = 1234
    manager.protect(pid)
    assert pid in manager._protected_pids

def test_protect_adds_min_pid():
    manager = ProcessManager()
    min_pid = 1
    manager.protect(min_pid)
    assert min_pid in manager._protected_pids

def test_protect_adds_max_pid():
    manager = ProcessManager()
    max_pid = 999999999
    manager.protect(max_pid)
    assert max_pid in manager._protected_pids

def test_protect_rejects_invalid_pid():
    manager = ProcessManager()
    invalid_pid = "invalid"
    manager.protect(invalid_pid)
    assert invalid_pid not in manager._protected_pids

def test_protect_rejects_none_pid():
    manager = ProcessManager()
    manager.protect(None)
    assert None not in manager._protected_pids

def test_protect_idempotent():
    manager = ProcessManager()
    pid = 1234
    manager.protect(pid)
    initial_size = len(manager._protected_pids)
    manager.protect(pid)
    assert len(manager._protected_pids) == initial_size

def test_protect_negative_pid():
    manager = ProcessManager()
    pid = -1
    manager.protect(pid)
    assert pid in manager._protected_pids