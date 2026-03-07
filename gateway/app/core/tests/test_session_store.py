import pytest
from unittest.mock import patch
import os

from gateway.app.core.session_store import SessionStore

def test_get_path_happy_path():
    session_store = SessionStore("/tmp")
    assert session_store._get_path("session123") == "/tmp/session123.json"

def test_get_path_empty_session_id():
    session_store = SessionStore("/tmp")
    assert session_store._get_path("") is None

def test_get_path_none_session_id():
    session_store = SessionStore("/tmp")
    assert session_store._get_path(None) is None

def test_get_path_boundary_long_session_id():
    session_store = SessionStore("/tmp")
    long_id = "a" * 1024
    safe_id = os.path.basename(long_id)
    expected_path = os.path.join("/tmp", f"{safe_id}.json")
    assert session_store._get_path(long_id) == expected_path

def test_get_path_boundary_long_base_dir():
    with patch.object(SessionStore, "base_dir", new="a" * 1024):
        session_store = SessionStore("b" * 1024)
        long_id = "c" * 1024
        safe_id = os.path.basename(long_id)
        expected_path = os.path.join("b" * 1024, f"{safe_id}.json")
        assert session_store._get_path(long_id) == expected_path