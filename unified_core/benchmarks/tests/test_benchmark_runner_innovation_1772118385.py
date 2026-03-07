import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from unified_core.benchmarks.benchmark_runner import BenchmarkRunner

def test_init_happy_path():
    runner = BenchmarkRunner()
    assert runner._default_max_steps == 5
    assert runner._default_timeout == 30.0
    assert runner._output_dir == Path("/tmp/noogh_safe/benchmark_results")
    assert not runner._shutdown_requested
    assert runner._adapter is None

def test_init_with_custom_values():
    runner = BenchmarkRunner(default_max_steps=10, default_timeout=60.0, output_dir="/path/to/output")
    assert runner._default_max_steps == 10
    assert runner._default_timeout == 60.0
    assert runner._output_dir == Path("/path/to/output")

def test_init_with_none_output_dir():
    runner = BenchmarkRunner(output_dir=None)
    assert runner._output_dir == Path("/tmp/noogh_safe/benchmark_results")

@patch('unified_core.benchmarks.benchmark_runner.logger.info')
def test_init_logger_info(mock_logger):
    BenchmarkRunner()
    mock_logger.assert_called_once_with("BenchmarkRunner initialized")