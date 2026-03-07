import pytest

from unified_core.centralized_logging_service import CentralizedLoggingService

@pytest.fixture
def logs_service():
    service = CentralizedLoggingService()
    service.logs = [
        {'level': 'info', 'source': 'app', 'message': 'Log 1'},
        {'level': 'error', 'source': 'db', 'message': 'Log 2'},
        {'level': 'info', 'source': 'app', 'message': 'Log 3'}
    ]
    return service

def test_filter_logs_happy_path(logs_service):
    filtered = logs_service.filter_logs(level='info')
    assert len(filtered) == 2
    assert all(log['level'] == 'info' for log in filtered)

def test_filter_logs_by_source(logs_service):
    filtered = logs_service.filter_logs(source='db')
    assert len(filtered) == 1
    assert all(log['source'] == 'db' for log in filtered)

def test_filter_logs_by_level_and_source(logs_service):
    filtered = logs_service.filter_logs(level='error', source='db')
    assert len(filtered) == 1
    assert all(log['level'] == 'error' and log['source'] == 'db' for log in filtered)

def test_filter_logs_empty_input(logs_service):
    filtered = logs_service.filter_logs()
    assert filtered == logs_service.logs

def test_filter_logs_none_level_source(logs_service):
    filtered = logs_service.filter_logs(level=None, source=None)
    assert filtered == logs_service.logs

def test_filter_logs_boundary_values(logs_service):
    # Assuming level and source are strings, check with boundary values
    filtered = logs_service.filter_logs(level='', source='')
    assert filtered == []

def test_filter_logs_invalid_input(logs_service):
    # Assuming no explicit exception is raised for invalid inputs,
    # this case will simply return the original list of logs.
    filtered = logs_service.filter_logs(level='unknown', source='app')
    assert filtered == []