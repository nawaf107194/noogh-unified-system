import pytest

from memory_storage.architecture_1771283668_1771638393 import MemoryStorage

def test_init_happy_path():
    db_connection = "fake_db_connection"
    instance = MemoryStorage(db_connection)
    assert instance.db_connection == db_connection

def test_init_edge_case_empty_string():
    db_connection = ""
    instance = MemoryStorage(db_connection)
    assert instance.db_connection == db_connection

def test_init_edge_case_none():
    db_connection = None
    instance = MemoryStorage(db_connection)
    assert instance.db_connection is None

def test_init_error_case_invalid_type():
    with pytest.raises(TypeError):
        db_connection = 12345
        instance = MemoryStorage(db_connection)