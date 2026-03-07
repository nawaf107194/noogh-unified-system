import pytest
from unified_core.benchmarks.benchmark_runner import BenchmarkRunner, BenchmarkResults, TaskDefinition

@pytest.fixture
def benchmark_runner():
    return BenchmarkRunner()

@pytest.fixture
def task_definition():
    return TaskDefinition(name="test_task", function=lambda: "result")

def test_happy_path(benchmark_runner, task_definition):
    runner = benchmark_runner
    tasks = [task_definition]
    result = runner.run_benchmark("test_benchmark", tasks)
    
    assert isinstance(result, BenchmarkResults)
    assert result.benchmark_name == "test_benchmark"
    assert result.total_tasks == 1
    assert result.completed_tasks == 1
    assert result.successful_tasks == 1
    assert result.failed_tasks == 0
    assert result.timeout_tasks == 0

def test_empty_tasks(benchmark_runner):
    runner = benchmark_runner
    tasks = []
    result = runner.run_benchmark("test_benchmark", tasks)
    
    assert isinstance(result, BenchmarkResults)
    assert result.benchmark_name == "test_benchmark"
    assert result.total_tasks == 0
    assert result.completed_tasks == 0
    assert result.successful_tasks == 0
    assert result.failed_tasks == 0
    assert result.timeout_tasks == 0

def test_none_tasks(benchmark_runner):
    runner = benchmark_runner
    tasks = None
    result = runner.run_benchmark("test_benchmark", tasks)
    
    assert isinstance(result, BenchmarkResults)
    assert result.benchmark_name == "test_benchmark"
    assert result.total_tasks == 0
    assert result.completed_tasks == 0
    assert result.successful_tasks == 0
    assert result.failed_tasks == 0
    assert result.timeout_tasks == 0

def test_single_task_failure(benchmark_runner, task_definition):
    runner = benchmark_runner
    
    class FailingTask(TaskDefinition):
        def __call__(self):
            raise Exception("Failed")
    
    tasks = [FailingTask()]
    result = runner.run_benchmark("test_benchmark", tasks)
    
    assert isinstance(result, BenchmarkResults)
    assert result.benchmark_name == "test_benchmark"
    assert result.total_tasks == 1
    assert result.completed_tasks == 1
    assert result.successful_tasks == 0
    assert result.failed_tasks == 1
    assert result.timeout_tasks == 0

def test_shutdown_requested(benchmark_runner, task_definition):
    runner = benchmark_runner
    
    class ShutdownTask(TaskDefinition):
        def __call__(self):
            return {"status": "completed", "success": True}
    
    tasks = [ShutdownTask()]
    with pytest.raises(SystemExit) as exc_info:
        runner._shutdown_requested = True
        runner.run_benchmark("test_benchmark", tasks)
        
    assert isinstance(exc_info.value, SystemExit)
    assert exc_info.value.code == 0

def test_async_behavior(benchmark_runner, task_definition):
    import asyncio
    
    class AsyncTask(TaskDefinition):
        async def __call__(self):
            await asyncio.sleep(0.1)
            return {"status": "completed", "success": True}
    
    tasks = [AsyncTask()]
    result = benchmark_runner.run_benchmark("test_benchmark", tasks)
    
    assert isinstance(result, BenchmarkResults)
    assert result.benchmark_name == "test_benchmark"
    assert result.total_tasks == 1
    assert result.completed_tasks == 1
    assert result.successful_tasks == 1
    assert result.failed_tasks == 0
    assert result.timeout_tasks == 0