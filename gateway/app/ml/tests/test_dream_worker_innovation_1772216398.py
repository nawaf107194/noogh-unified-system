import pytest

from gateway.app.ml.dream_worker import DreamWorker, PriorityDreamScheduler

def test_dream_worker_init_happy_path():
    scheduler = PriorityDreamScheduler()
    dream_worker = DreamWorker(scheduler)
    assert dream_worker.scheduler == scheduler
    assert dream_worker.teacher is None
    assert not dream_worker.is_active

def test_dream_worker_init_with_none_scheduler():
    with pytest.raises(TypeError):
        DreamWorker(None)

def test_dream_worker_init_with_empty_string_as_scheduler():
    with pytest.raises(TypeError):
        DreamWorker('')

def test_dream_worker_init_with_integer_as_scheduler():
    with pytest.raises(TypeError):
        DreamWorker(123)