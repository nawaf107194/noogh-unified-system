import pytest

from scripts.performance_monitor import main, PerformanceMonitor

@pytest.fixture
def parser():
    from argparse import ArgumentParser
    return ArgumentParser()

def test_main_happy_path(parser):
    args = ['--interval', '10']
    with pytest.raises(SystemExit) as exc_info:
        main(['performance_monitor.py'] + args)
    assert exc_info.value.code == 0

def test_main_edge_case_empty_args(parser):
    args = []
    with pytest.raises(SystemExit) as exc_info:
        main(['performance_monitor.py'] + args)
    assert exc_info.value.code == 0

def test_main_edge_case_none_interval(parser):
    args = ['--interval', 'None']
    with pytest.raises(SystemExit) as exc_info:
        main(['performance_monitor.py'] + args)
    assert exc_info.value.code == 0

def test_main_edge_case_once(parser, monkeypatch):
    args = ['--once']
    
    # Mock PerformanceMonitor methods
    mock_metrics = {'cpu': 25.0, 'memory': 75.0}
    
    def mock_collect_metrics():
        return mock_metrics
    
    def mock_print_current_status(metrics):
        pass
    
    def mock_save_metrics(metrics):
        pass

    monkeypatch.setattr(PerformanceMonitor, 'collect_metrics', mock_collect_metrics)
    monkeypatch.setattr(PerformanceMonitor, 'print_current_status', mock_print_current_status)
    monkeypatch.setattr(PerformanceMonitor, 'save_metrics', mock_save_metrics)

    with pytest.raises(SystemExit) as exc_info:
        main(['performance_monitor.py'] + args)
    assert exc_info.value.code == 0

def test_main_error_case_invalid_interval(parser):
    args = ['--interval', '-1']
    with pytest.raises(SystemExit) as exc_info:
        main(['performance_monitor.py'] + args)
    assert exc_info.value.code == 2

def test_main_async_behavior(parser, monkeypatch):
    args = ['--interval', '10']

    # Mock PerformanceMonitor methods
    mock_metrics = {'cpu': 25.0, 'memory': 75.0}
    
    def mock_collect_metrics():
        return mock_metrics
    
    def mock_print_current_status(metrics):
        pass
    
    def mock_save_metrics(metrics):
        pass

    monkeypatch.setattr(PerformanceMonitor, 'collect_metrics', mock_collect_metrics)
    monkeypatch.setattr(PerformanceMonitor, 'print_current_status', mock_print_current_status)
    monkeypatch.setattr(PerformanceMonitor, 'save_metrics', mock_save_metrics)

    import time
    start_time = time.time()
    with pytest.raises(SystemExit) as exc_info:
        main(['performance_monitor.py'] + args)
    end_time = time.time()

    assert (end_time - start_time) >= 10