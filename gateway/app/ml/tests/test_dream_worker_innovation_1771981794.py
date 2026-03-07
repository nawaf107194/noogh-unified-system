import pytest

from gateway.app.ml.dream_worker import DreamWorker, PriorityDreamScheduler

class MockPriorityDreamScheduler:
    def __init__(self):
        pass

def test_happy_path():
    scheduler = MockPriorityDreamScheduler()
    worker = DreamWorker(scheduler)
    
    assert isinstance(worker.scheduler, PriorityDreamScheduler)
    assert worker.teacher is None
    assert not worker.is_active

def test_edge_case_none_scheduler():
    with pytest.raises(TypeError) as exc_info:
        worker = DreamWorker(None)
    
    assert str(exc_info.value) == "scheduler must be an instance of PriorityDreamScheduler"

def test_error_case_invalid_scheduler_type():
    class InvalidScheduler:
        pass
    
    scheduler = InvalidScheduler()
    with pytest.raises(TypeError) as exc_info:
        worker = DreamWorker(scheduler)
    
    assert str(exc_info.value) == "scheduler must be an instance of PriorityDreamScheduler"