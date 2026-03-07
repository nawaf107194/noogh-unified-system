import pytest

from gateway.app.core.worker import Worker

def test_stop_happy_path():
    worker = Worker()
    worker.running = True
    worker.executor = Mock()

    worker.stop()

    assert not worker.running
    assert worker.executor.shutdown.call_count == 1

def test_stop_edge_case_none_executor():
    worker = Worker()
    worker.running = True
    worker.executor = None

    worker.stop()

    assert not worker.running
    # No assertion needed for executor.shutdown as it's None

def test_stop_async_behavior():
    worker = Worker()
    worker.running = True
    worker.executor = Mock()
    
    future = ConcurrentFuture()
    worker.executor.shutdown.side_effect = lambda wait: None
    
    with pytest.raises(TimeoutError):
        worker.stop(wait=True, timeout=0.1)
    
    assert not worker.running
    assert worker.executor.shutdown.call_count == 1