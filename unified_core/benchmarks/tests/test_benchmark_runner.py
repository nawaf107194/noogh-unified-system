import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Assuming BenchmarkRunner is defined in unified_core/benchmarks/benchmark_runner.py
from unified_core.benchmarks.benchmark_runner import BenchmarkRunner, main

def test_main_happy_path():
    with patch('sys.argv', ["main", "--bench=toolbench_local", "--tasks=50", "--timeout=30.0", "--json-out=/tmp/noogh_safe/output.json"]):
        with patch.object(BenchmarkRunner, 'run_toolbench_local') as mock_run_toolbench:
            mock_run_toolbench.return_value = {"status": "success"}
            with patch.object(BenchmarkRunner, 'print_report') as mock_print_report:
                with patch.object(BenchmarkRunner, 'save_results') as mock_save_results:
                    main()
                    mock_run_toolbench.assert_called_once_with(50)
                    mock_print_report.assert_called_once_with({"status": "success"})
                    mock_save_results.assert_called_once_with({"status": "success"}, "/tmp/noogh_safe/output.json")

def test_main_all_benchmarks():
    with patch('sys.argv', ["main", "--bench=all"]):
        with patch.object(BenchmarkRunner, 'run_toolbench_local') as mock_run_toolbench:
            mock_run_toolbench.return_value = {"status": "success"}
            with patch.object(BenchmarkRunner, 'print_report') as mock_print_report:
                with patch.object(BenchmarkRunner, 'save_results') as mock_save_results:
                    main()
                    mock_run_toolbench.assert_called_once_with(50)
                    mock_print_report.assert_called_once_with({"status": "success"})
                    mock_save_results.assert_called_once_with({"status": "success"})

def test_main_agentbench_local():
    with patch('sys.argv', ["main", "--bench=agentbench_local"]):
        with patch.object(BenchmarkRunner, 'run_agentbench_local') as mock_run_agentbench:
            mock_run_agentbench.return_value = {"status": "success"}
            with patch.object(BenchmarkRunner, 'print_report') as mock_print_report:
                with patch.object(BenchmarkRunner, 'save_results') as mock_save_results:
                    main()
                    mock_run_agentbench.assert_called_once()
                    mock_print_report.assert_called_once_with({"status": "success"})
                    mock_save_results.assert_called_once_with({"status": "success"})

def test_main_no_benchmark():
    with patch('sys.argv', ["main"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2

def test_main_invalid_benchmark():
    with patch('sys.argv', ["main", "--bench=invalid_bench"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2

def test_main_negative_tasks():
    with patch('sys.argv', ["main", "--tasks=-10"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2

def test_main_zero_tasks():
    with patch('sys.argv', ["main", "--tasks=0"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2

def test_main_large_timeout():
    with patch('sys.argv', ["main", "--timeout=100.0"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2

def test_main_negative_timeout():
    with patch('sys.argv', ["main", "--timeout=-30.0"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2

def test_main_zero_timeout():
    with patch('sys.argv', ["main", "--timeout=0.0"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2