import pytest
from pathlib import Path
from typing import Optional

class UnifiedCoreRuntime:
    def __init__(self, src_dir: Optional[str] = None):
        self.src_dir = Path(src_dir or Path(__file__).resolve().parents[1])
        self.processes: Dict[str, subprocess.Popen] = {}
        self.shutdown_event = asyncio.Event()
        self._loop = None

@pytest.fixture
def runtime():
    return UnifiedCoreRuntime()

def test_happy_path(runtime):
    assert isinstance(runtime.src_dir, Path)
    assert 'unified_system' in str(runtime.src_dir)
    assert isinstance(runtime.processes, dict)
    assert isinstance(runtime.shutdown_event, asyncio.Event)
    assert runtime._loop is None

def test_edge_case_empty_string(runtime):
    runtime = UnifiedCoreRuntime(src_dir='')
    assert isinstance(runtime.src_dir, Path)
    assert 'unified_system' in str(runtime.src_dir)

def test_edge_case_none(runtime):
    runtime = UnifiedCoreRuntime(src_dir=None)
    assert isinstance(runtime.src_dir, Path)
    assert 'unified_system' in str(runtime.src_dir)

def test_error_case_invalid_path(runtime):
    with pytest.raises(FileNotFoundError):
        UnifiedCoreRuntime(src_dir='/nonexistent/path')