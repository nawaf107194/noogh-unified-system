import pytest
from pathlib import Path
import asyncio
from unified_core.runtime import UnifiedCore

def test_happy_path():
    runtime = UnifiedCore(src_dir="/path/to/src")
    assert isinstance(runtime.src_dir, Path)
    assert runtime.src_dir == Path("/path/to/src")
    assert isinstance(runtime.processes, dict)
    assert runtime.processes == {}
    assert isinstance(runtime.shutdown_event, asyncio.Event)
    assert not runtime.shutdown_event.is_set()
    assert runtime._loop is None

def test_empty_src_dir():
    runtime = UnifiedCore(src_dir="")
    assert isinstance(runtime.src_dir, Path)
    assert runtime.src_dir == Path(__file__).resolve().parents[1]
    assert isinstance(runtime.processes, dict)
    assert runtime.processes == {}
    assert isinstance(runtime.shutdown_event, asyncio.Event)
    assert not runtime.shutdown_event.is_set()
    assert runtime._loop is None

def test_none_src_dir():
    runtime = UnifiedCore(src_dir=None)
    assert isinstance(runtime.src_dir, Path)
    assert runtime.src_dir == Path(__file__).resolve().parents[1]
    assert isinstance(runtime.processes, dict)
    assert runtime.processes == {}
    assert isinstance(runtime.shutdown_event, asyncio.Event)
    assert not runtime.shutdown_event.is_set()
    assert runtime._loop is None

def test_boundary_src_dir():
    # Assuming the boundary case for src_dir is too long
    long_path = "a" * 1024  # Adjust based on actual maximum length
    runtime = UnifiedCore(src_dir=long_path)
    assert isinstance(runtime.src_dir, Path)
    assert runtime.src_dir == Path(long_path)
    assert isinstance(runtime.processes, dict)
    assert runtime.processes == {}
    assert isinstance(runtime.shutdown_event, asyncio.Event)
    assert not runtime.shutdown_event.is_set()
    assert runtime._loop is None

def test_error_cases():
    # Since the code does not explicitly raise errors for invalid inputs,
    # we will only test for unexpected behavior.
    
    with pytest.raises(TypeError):
        UnifiedCore(src_dir=123)  # Non-string input

    with pytest.raises(ValueError):
        UnifiedCore(src_dir="/nonexistent/path")  # Non-existent directory