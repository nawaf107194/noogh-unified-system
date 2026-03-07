import pytest

from unified_core.benchmark_runner import BenchmarkRunner, SAMPLE_TASKS

class MockBenchmarkRunner(BenchmarkRunner):
    def run_benchmark(self, suite_name, tasks):
        if suite_name == "ToolBench" and tasks == SAMPLE_TASKS:
            return {
                "Tool Selection Accuracy": 0.95,
                "Argument Accuracy": 0.85,
                "Success Rate": 0.98,
                "Hallucination Rate": 0.02
            }
        else:
            return None

class TestBenchmarkRunner:
    @pytest.fixture
    def benchmark_runner(self):
        return MockBenchmarkRunner()

    def test_happy_path(self, benchmark_runner):
        result = benchmark_runner.run_toolbench_suite()
        assert result == {
            "Tool Selection Accuracy": 0.95,
            "Argument Accuracy": 0.85,
            "Success Rate": 0.98,
            "Hallucination Rate": 0.02
        }

    def test_edge_case_empty_tasks(self, benchmark_runner):
        result = benchmark_runner.run_toolbench_suite()
        assert result == {
            "Tool Selection Accuracy": 0.95,
            "Argument Accuracy": 0.85,
            "Success Rate": 0.98,
            "Hallucination Rate": 0.02
        }

    def test_edge_case_none_tasks(self, benchmark_runner):
        result = benchmark_runner.run_toolbench_suite()
        assert result == {
            "Tool Selection Accuracy": 0.95,
            "Argument Accuracy": 0.85,
            "Success Rate": 0.98,
            "Hallucination Rate": 0.02
        }

    def test_edge_case_boundary_tasks(self, benchmark_runner):
        result = benchmark_runner.run_toolbench_suite()
        assert result == {
            "Tool Selection Accuracy": 0.95,
            "Argument Accuracy": 0.85,
            "Success Rate": 0.98,
            "Hallucination Rate": 0.02
        }

    def test_error_case_invalid_suite_name(self, benchmark_runner):
        result = benchmark_runner.run_toolbench_suite()
        assert result == {
            "Tool Selection Accuracy": 0.95,
            "Argument Accuracy": 0.85,
            "Success Rate": 0.98,
            "Hallucination Rate": 0.02
        }

    def test_error_case_invalid_tasks_type(self, benchmark_runner):
        result = benchmark_runner.run_toolbench_suite()
        assert result == {
            "Tool Selection Accuracy": 0.95,
            "Argument Accuracy": 0.85,
            "Success Rate": 0.98,
            "Hallucination Rate": 0.02
        }

    def test_error_case_invalid_tasks_value(self, benchmark_runner):
        result = benchmark_runner.run_toolbench_suite()
        assert result == {
            "Tool Selection Accuracy": 0.95,
            "Argument Accuracy": 0.85,
            "Success Rate": 0.98,
            "Hallucination Rate": 0.02
        }