import pytest
from unittest.mock import patch, Mock

from src.scripts.health_check import main, get_system_health_monitor

def test_main_happy_path():
    with patch('src.scripts.health_check.get_system_health_monitor') as mock_get_monitor:
        monitor_result = {
            'status': 'healthy',
            'issues': []
        }
        mock_get_monitor.return_value.run_all_checks.return_value = monitor_result
        result = main()
        assert result == 0
        print("Happy path test passed.")

def test_main_critical_issues():
    with patch('src.scripts.health_check.get_system_health_monitor') as mock_get_monitor:
        monitor_result = {
            'status': 'critical',
            'issues': [
                {'severity': 'critical', 'message': 'Issue 1', 'fix_suggestion': 'Fix 1'},
                {'severity': 'warning', 'message': 'Issue 2'}
            ]
        }
        mock_get_monitor.return_value.run_all_checks.return_value = monitor_result
        result = main()
        assert result == 1
        print("Critical issues test passed.")

def test_main_warnings():
    with patch('src.scripts.health_check.get_system_health_monitor') as mock_get_monitor:
        monitor_result = {
            'status': 'warning',
            'issues': [
                {'severity': 'critical', 'message': 'Issue 1'},
                {'severity': 'warning', 'message': 'Issue 2', 'fix_suggestion': 'Fix 2', 'auto_fixable': True}
            ]
        }
        mock_get_monitor.return_value.run_all_checks.return_value = monitor_result
        result = main()
        assert result == 0
        print("Warnings test passed.")

def test_main_empty_issues():
    with patch('src.scripts.health_check.get_system_health_monitor') as mock_get_monitor:
        monitor_result = {
            'status': 'unknown',
            'issues': []
        }
        mock_get_monitor.return_value.run_all_checks.return_value = monitor_result
        result = main()
        assert result == 0
        print("Empty issues test passed.")

def test_main_none_status():
    with patch('src.scripts.health_check.get_system_health_monitor') as mock_get_monitor:
        monitor_result = {
            'status': None,
            'issues': []
        }
        mock_get_monitor.return_value.run_all_checks.return_value = monitor_result
        result = main()
        assert result == 0
        print("None status test passed.")

def test_main_none_issues():
    with patch('src.scripts.health_check.get_system_health_monitor') as mock_get_monitor:
        monitor_result = {
            'status': 'healthy',
            'issues': None
        }
        mock_get_monitor.return_value.run_all_checks.return_value = monitor_result
        result = main()
        assert result == 0
        print("None issues test passed.")

def test_main_empty_status():
    with patch('src.scripts.health_check.get_system_health_monitor') as mock_get_monitor:
        monitor_result = {
            'status': '',
            'issues': []
        }
        mock_get_monitor.return_value.run_all_checks.return_value = monitor_result
        result = main()
        assert result == 0
        print("Empty status test passed.")

def test_main_empty_issues_list():
    with patch('src.scripts.health_check.get_system_health_monitor') as mock_get_monitor:
        monitor_result = {
            'status': 'healthy',
            'issues': []
        }
        mock_get_monitor.return_value.run_all_checks.return_value = monitor_result
        result = main()
        assert result == 0
        print("Empty issues list test passed.")