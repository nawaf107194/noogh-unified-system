import pytest

from unified_core.benchmarks.benchmark_runner import BenchmarkRunner, TOOLBENCH_LOCAL_TASKS, BenchmarkResults

@pytest.fixture
def benchmark_runner():
    return BenchmarkRunner()

def test_run_toolbench_local_happy_path(benchmark_runner):
    # Arrange
    num_tasks = 10
    
    # Act
    result = benchmark_runner.run_toolbench_local(num_tasks)
    
    # Assert
    assert isinstance(result, BenchmarkResults)
    assert len(result) == num_tasks

def test_run_toolbench_local_edge_case_empty(benchmark_runner):
    # Arrange
    num_tasks = 0
    
    # Act
    result = benchmark_runner.run_toolbench_local(num_tasks)
    
    # Assert
    assert isinstance(result, BenchmarkResults)
    assert len(result) == 0

def test_run_toolbench_local_edge_case_none(benchmark_runner):
    # Arrange
    num_tasks = None
    
    # Act
    result = benchmark_runner.run_toolbench_local(num_tasks)
    
    # Assert
    assert isinstance(result, BenchmarkResults)
    assert len(result) == 50

def test_run_toolbench_local_error_case_negative(benchmark_runner):
    # Arrange
    num_tasks = -1
    
    # Act
    result = benchmark_runner.run_toolbench_local(num_tasks)
    
    # Assert
    assert isinstance(result, BenchmarkResults)
    assert len(result) == 50

def test_run_toolbench_local_edge_case_boundary_max(benchmark_runner):
    # Arrange
    num_tasks = len(TOOLBench_LOCAL_TASKS)
    
    # Act
    result = benchmark_runner.run_toolbench_local(num_tasks)
    
    # Assert
    assert isinstance(result, BenchmarkResults)
    assert len(result) == num_tasks

def test_run_toolbench_local_edge_case_boundary_min(benchmark_runner):
    # Arrange
    num_tasks = 1
    
    # Act
    result = benchmark_runner.run_toolbench_local(num_tasks)
    
    # Assert
    assert isinstance(result, BenchmarkResults)
    assert len(result) == num_tasks