import pytest
from unittest.mock import patch, MagicMock

# Assuming get_system_health_monitor is a function that should return an object with run_all_checks method
class MockMonitor:
    def __init__(self):
        self.issues = []

    def run_all_checks(self):
        return {
            "status": "healthy",
            "issues": self.issues
        }

@pytest.fixture
def mock_monitor():
    return MockMonitor()

@patch('health_check.get_system_health_monitor')
def test_happy_path(mock_get_system_health_monitor, mock_monitor):
    mock_get_system_health_monitor.return_value = mock_monitor

    result = main()
    
    assert result == 0
    assert "✔️ HEALTHY" in capsys.readouterr().out
    assert "All systems nominal!" in capsys.readouterr().out

@patch('health_check.get_system_health_monitor')
def test_edge_case_empty_issues(mock_get_system_health_monitor, mock_monitor):
    mock_monitor.issues = []
    mock_get_system_health_monitor.return_value = mock_monitor

    result = main()
    
    assert result == 0
    assert "✔️ HEALTHY" in capsys.readouterr().out
    assert "All systems nominal!" in capsys.readouterr().out

@patch('health_check.get_system_health_monitor')
def test_edge_case_critical_issues(mock_get_system_health_monitor, mock_monitor):
    mock_monitor.issues = [
        {"severity": "critical", "message": "Disk space low", "fix_suggestion": "Run cleanup"}
    ]
    mock_get_system_health_monitor.return_value = mock_monitor

    result = main()
    
    assert result == 1
    assert "🚨 CRITICAL ISSUES (1):" in capsys.readouterr().out
    assert "❌ Disk space low" in capsys.readouterr().out
    assert "💡 Fix: Run cleanup" in capsys.readouterr().out

@patch('health_check.get_system_health_monitor')
def test_edge_case_warnings(mock_get_system_health_monitor, mock_monitor):
    mock_monitor.issues = [
        {"severity": "warning", "message": "CPU usage high"}
    ]
    mock_get_system_health_monitor.return_value = mock_monitor

    result = main()
    
    assert result == 0
    assert "⚠️  WARNINGS (1):" in capsys.readouterr().out
    assert "⚠️  CPU usage high" in capsys.readouterr().out

@patch('health_check.get_system_health_monitor')
def test_error_case_none_result(mock_get_system_health_monitor):
    mock_get_system_health_monitor.return_value = None

    result = main()
    
    assert result == 1
    assert "❓ Unknown" in capsys.readouterr().out

@pytest.mark.parametrize("mock_issues", [
    [],
    [{"severity": "critical", "message": "Disk space low"}],
    [{"severity": "warning", "message": "CPU usage high"}]
])
@patch('health_check.get_system_health_monitor')
def test_async_behavior(mock_get_system_health_monitor, mock_monitor):
    mock_get_system_health_monitor.return_value = mock_monitor
    mock_monitor.issues = mock_issues

    result = main()
    
    if mock_issues and any(issue['severity'] == 'critical' for issue in mock_issues):
        assert result == 1
    else:
        assert result == 0

    # Check the output based on issues
    critical_count = sum(1 for issue in mock_issues if issue['severity'] == 'critical')
    warning_count = sum(1 for issue in mock_issues if issue['severity'] == 'warning')

    assert f"Total Issues: {len(mock_issues)} ({critical_count} critical, {warning_count} warnings)" in capsys.readouterr().out