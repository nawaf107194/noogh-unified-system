import pytest
from unittest.mock import patch, MagicMock
from unified_core.benchmark_runner import main as runner_main, BenchmarkRunner
import argparse
import sys
import json
import logging

def test_happy_path(capsys):
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        mock_args = MagicMock()
        mock_args.benchmark = "all"
        mock_args.task_id = None
        mock_args.timeout = 300.0
        mock_args.output_dir = "/tmp/results"
        mock_parse_args.return_value = mock_args
        
        with patch('unified_core.benchmark_runner.BenchmarkRunner') as MockBenchmarkRunner:
            mock_runner = MockBenchmarkRunner()
            mock_runner.run_agentbench_suite.return_value = [{'benchmark_name': 'AgentBench', 'success_rate': 0.7}]
            mock_runner.run_toolbench_suite.return_value = [{'benchmark_name': 'ToolBench', 'avg_hallucination_rate': 0.05}]
            mock_runner.run_failure_tests.return_value = [{'benchmark_name': 'FailureTests'}]
            mock_runner.generate_report.side_effect = lambda x: json.dumps(x)
            mock_runner.save_results.side_effect = lambda x: None
            mock_runner.shutdown.side_effect = lambda: None
            
            runner_main()
            
            captured = capsys.readouterr()
            assert "FINAL SYSTEM VERDICT" in captured.out

def test_edge_case_task_id(capsys):
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        mock_args = MagicMock()
        mock_args.benchmark = None
        mock_args.task_id = "task1"
        mock_args.timeout = 300.0
        mock_args.output_dir = "/tmp/results"
        mock_parse_args.return_value = mock_args
        
        with patch('unified_core.benchmark_runner.BenchmarkRunner') as MockBenchmarkRunner:
            mock_runner = MockBenchmarkRunner()
            mock_runner.run_single_task.return_value = {'task_id': 'task1', 'result': 'success'}
            
            runner_main()
            
            captured = capsys.readouterr()
            assert "Task not found" in captured.out

def test_error_case_invalid_benchmark(capsys):
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        mock_args = MagicMock()
        mock_args.benchmark = "invalid"
        mock_args.task_id = None
        mock_args.timeout = 300.0
        mock_args.output_dir = "/tmp/results"
        mock_parse_args.return_value = mock_args
        
        with patch('unified_core.benchmark_runner.BenchmarkRunner') as MockBenchmarkRunner:
            runner_main()
            
            captured = capsys.readouterr()
            assert "error: argument --benchmark: invalid choice" in captured.out

def test_async_behavior(capsys):
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        mock_args = MagicMock()
        mock_args.benchmark = "all"
        mock_args.task_id = None
        mock_args.timeout = 300.0
        mock_args.output_dir = "/tmp/results"
        mock_parse_args.return_value = mock_args
        
        with patch('unified_core.benchmark_runner.asyncio') as MockAsyncio:
            async def fake_async_task():
                return True
            
            MockAsyncio.sleep.side_effect = lambda x: None
            MockAsyncio.create_task.side_effect = lambda task: task()
            
            with patch('unified_core.benchmark_runner.BenchmarkRunner') as MockBenchmarkRunner:
                mock_runner = MockBenchmarkRunner()
                mock_runner.run_agentbench_suite.return_value = [{'benchmark_name': 'AgentBench', 'success_rate': 0.7}]
                mock_runner.run_toolbench_suite.return_value = [{'benchmark_name': 'ToolBench', 'avg_hallucination_rate': 0.05}]
                mock_runner.run_failure_tests.return_value = [{'benchmark_name': 'FailureTests'}]
                mock_runner.generate_report.side_effect = lambda x: json.dumps(x)
                mock_runner.save_results.side_effect = lambda x: None
                mock_runner.shutdown.side_effect = lambda: None
                
                runner_main()
                
                captured = capsys.readouterr()
                assert "FINAL SYSTEM VERDICT" in captured.out