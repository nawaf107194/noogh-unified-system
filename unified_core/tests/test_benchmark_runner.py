from unified_core.benchmark_runner import BenchmarkRunner, SAMPLE_TASKS, BenchmarkResults

@pytest.fixture
def runner():
    return BenchmarkRunner()

def test_run_toolbench_suite_happy_path(runner):
    # Happy path with normal inputs
    result = runner.run_toolbench_suite()
    assert isinstance(result, BenchmarkResults)
    assert hasattr(result, 'tool_selection_accuracy')
    assert hasattr(result, 'argument_accuracy')
    assert hasattr(result, 'success_rate')
    assert hasattr(result, 'hallucination_rate')

def test_run_toolbench_suite_empty_tasks(runner):
    runner.tasks = []
    result = runner.run_toolbench_suite()
    assert isinstance(result, BenchmarkResults)
    assert result.tool_selection_accuracy == 0
    assert result.argument_accuracy == 0
    assert result.success_rate == 0
    assert result.hallucination_rate == 0

def test_run_toolbench_suite_none_tasks(runner):
    runner.tasks = None
    result = runner.run_toolbench_suite()
    assert isinstance(result, BenchmarkResults)
    assert result.tool_selection_accuracy == 0
    assert result.argument_accuracy == 0
    assert result.success_rate == 0
    assert result.hallucination_rate == 0

def test_run_toolbench_suite_boundary_tasks(runner):
    runner.tasks = [SAMPLE_TASKS[0]] * 100  # Boundary condition: many tasks
    result = runner.run_toolbench_suite()
    assert isinstance(result, BenchmarkResults)
    assert result.tool_selection_accuracy >= 0 and result.tool_selection_accuracy <= 1
    assert result.argument_accuracy >= 0 and result.argument_accuracy <= 1
    assert result.success_rate >= 0 and result.success_rate <= 1
    assert result.hallucination_rate >= 0 and result.hallucination_rate <= 1

def test_run_toolbench_suite_invalid_input(runner):
    runner.tasks = "invalid input"
    result = runner.run_toolbench_suite()
    assert isinstance(result, BenchmarkResults)
    assert result.tool_selection_accuracy == 0
    assert result.argument_accuracy == 0
    assert result.success_rate == 0
    assert result.hallucination_rate == 0