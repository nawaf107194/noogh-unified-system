import pytest

from shared.async_task_scheduler import AsyncTaskScheduler

def test_stop_happy_path():
    scheduler = AsyncTaskScheduler()
    # Schedule some tasks to ensure they are cleared
    for i in range(5):
        scheduler.schedule(f"task_{i}", lambda x: None)
    assert len(scheduler.tasks) > 0
    
    scheduler.stop()
    assert not scheduler.tasks
    assert not scheduler.loop.is_running()

def test_stop_empty_tasks():
    scheduler = AsyncTaskScheduler()
    scheduler.stop()
    assert not scheduler.tasks
    assert not scheduler.loop.is_running()

def test_stop_none_loop():
    scheduler = AsyncTaskScheduler()
    scheduler.loop = None
    scheduler.stop()
    # No assertion needed for None loop, as it's a normal behavior

def test_stop_async_behavior():
    import asyncio

    scheduler = AsyncTaskScheduler()
    async def task_to_cancel(task_id):
        await asyncio.sleep(1)
    
    task = scheduler.schedule("task_to_cancel", task_to_cancel)
    await asyncio.sleep(0.5)  # Ensure the task has some time to start
    scheduler.stop()

    with pytest.raises(asyncio.CancelledError):
        await task

# This test might need adjustment depending on how the loop is implemented