import pytest

from runpod_teacher.architecture_base import ArchitectureBase

def test_shutdown_happy_path():
    # Test normal shutdown
    obj = ArchitectureBase()
    result = obj.shutdown()
    assert result is None