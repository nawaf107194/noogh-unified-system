import pytest

from shared.performance_profiler import PerformanceProfiler

def test_happy_path():
    profiler = PerformanceProfiler(filename="test_profile.txt")
    assert profiler.filename == "test_profile.txt"
    assert profiler.pr is None

def test_empty_filename():
    profiler = PerformanceProfiler(filename="")
    assert profiler.filename == ""
    assert profiler.pr is None

def test_none_filename():
    profiler = PerformanceProfiler(filename=None)
    assert profiler.filename is None
    assert profiler.pr is None

def test_boundary_values():
    profiler = PerformanceProfiler(filename="1234567890" * 10)  # Assuming no length limit
    assert profiler.filename == "1234567890" * 10
    assert profiler.pr is None

# Error cases are not applicable as the function does not raise any exceptions explicitly.