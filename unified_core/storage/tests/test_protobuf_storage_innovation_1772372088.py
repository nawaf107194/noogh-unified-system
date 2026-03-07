import pytest

from unified_core.storage.protobuf_storage import _human_size

def test_human_size_happy_path():
    assert _human_size(1023) == "1023.0 B"
    assert _human_size(1024) == "1.0 KB"
    assert _human_size(1024**2) == "1.0 MB"
    assert _human_size(1024**3) == "1.0 GB"

def test_human_size_edge_cases():
    assert _human_size(0) == "0.0 B"
    assert _human_size(None) is None
    assert _human_size("") is None

def test_human_size_error_cases():
    with pytest.raises(TypeError):
        _human_size("not_an_int")

def test_human_size_async_behavior():
    # Assuming no async behavior in this function, so omitting this part
    pass