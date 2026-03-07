import pytest
from shared.async_task_scheduler import AsyncTaskScheduler

def test_add_task_happy_path():
    scheduler = AsyncTaskScheduler()
    def sample_task(x):
        return x * 2
    result = scheduler.add_task(sample_task, args=(5,))
    assert callable(result)
    assert len(scheduler.tasks) == 1

def test_add_task_empty_args():
    scheduler = AsyncTaskScheduler()
    def sample_task():
        return "hello"
    result = scheduler.add_task(sample_task)
    assert callable(result)
    assert len(scheduler.tasks) == 1

def test_add_task_boundary_values():
    scheduler = AsyncTaskScheduler()
    def sample_task(x):
        return x + 1
    result = scheduler.add_task(sample_task, args=(0,))
    assert callable(result)
    assert len(scheduler.tasks) == 1

def test_add_task_no_args():
    scheduler = AsyncTaskScheduler()
    def sample_task():
        return "default"
    result = scheduler.add_task(sample_task)
    assert callable(result)
    assert len(scheduler.tasks) == 1

def test_add_task_with_kwargs():
    scheduler = AsyncTaskScheduler()
    def sample_task(x, y):
        return x + y
    result = scheduler.add_task(sample_task, kwargs={'x': 3, 'y': 4})
    assert callable(result)
    assert len(scheduler.tasks) == 1

def test_add_task_with_complex_args():
    scheduler = AsyncTaskScheduler()
    def sample_task(lst):
        return lst[0]
    result = scheduler.add_task(sample_task, args=([1, 2, 3],))
    assert callable(result)
    assert len(scheduler.tasks) == 1