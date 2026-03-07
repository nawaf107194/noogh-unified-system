import pytest

from src.shared.async_task_scheduler import AsyncTaskScheduler

@pytest.fixture
def scheduler():
    return AsyncTaskScheduler()

async def dummy_task(arg):
    return arg * 2

async def test_happy_path(scheduler):
    result = await scheduler.add_task(dummy_task, 5)
    assert result is None
    assert len(scheduler.tasks) == 1
    assert callable(scheduler.tasks[0])
    assert await scheduler.tasks[0]() == 10

async def test_edge_cases_empty_inputs(scheduler):
    result = await scheduler.add_task(None)
    assert result is None
    assert len(scheduler.tasks) == 1
    assert callable(scheduler.tasks[0])

    result = await scheduler.add_task(lambda: None, [])
    assert result is None
    assert len(scheduler.tasks) == 2
    assert callable(scheduler.tasks[1])

async def test_error_cases_invalid_inputs(scheduler):
    with pytest.raises(ValueError):
        await scheduler.add_task("not a function")

async def test_async_behavior(scheduler, event_loop):
    async def async_dummy_task():
        return "Async task executed"

    result = await scheduler.add_task(async_dummy_task)
    assert result is None
    assert len(scheduler.tasks) == 1
    assert callable(scheduler.tasks[0])
    assert await scheduler.tasks[0]() == "Async task executed"