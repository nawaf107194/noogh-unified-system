import pytest

from shared.performance_profiler import PerformanceProfiler

def test_init_with_valid_filename():
    profiler = PerformanceProfiler(filename="example.txt")
    assert profiler.filename == "example.txt"
    assert profiler.pr is None

def test_init_with_empty_string():
    profiler = PerformanceProfiler(filename="")
    assert profiler.filename == ""
    assert profiler.pr is None

def test_init_with_none():
    profiler = PerformanceProfiler(filename=None)
    assert profiler.filename is None
    assert profiler.pr is None

# Assuming the class does not raise any exceptions with invalid inputs
def test_init_with_invalid_input():
    profiler = PerformanceProfiler(filename=12345)  # Invalid input type, assuming no exception raised
    assert profiler.filename == 12345
    assert profiler.pr is None

# If the class could potentially raise an exception for invalid inputs
# def test_init_with_invalid_input_raises_exception():
#     with pytest.raises(ValueError):
#         PerformanceProfiler(filename=12345)  # assuming ValueError is raised for invalid input type