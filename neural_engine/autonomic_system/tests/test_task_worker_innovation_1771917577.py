import pytest

from neural_engine.autonomic_system.task_worker import TaskWorker

def test_task_worker_init_happy_path():
    worker = TaskWorker()
    assert not worker.running
    assert worker.cycle_count == 0
    assert worker._initiative is None
    assert worker._governor is None
    assert worker._dream is None

def test_task_worker_init_edge_cases_none_values():
    worker = TaskWorker(None, None, None)
    assert not worker.running
    assert worker.cycle_count == 0
    assert worker._initiative is None
    assert worker._governor is None
    assert worker._dream is None

@pytest.mark.asyncio
async def test_task_worker_init_async_behavior():
    async def mock_governor():
        await asyncio.sleep(1)
        return True
    
    async def mock_dream():
        await asyncio.sleep(1)
        return False

    TaskWorker._governor = mock_governor
    TaskWorker._dream = mock_dream

    worker = TaskWorker()
    assert not worker.running
    assert worker.cycle_count == 0
    assert worker._initiative is None
    assert isinstance(worker._governor, asyncio.Coroutine)
    assert isinstance(worker._dream, asyncio.Coroutine)