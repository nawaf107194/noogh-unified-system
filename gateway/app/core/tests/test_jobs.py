import pytest

from gateway.app.core.jobs import list_queued_jobs

@pytest.fixture
def mock_redis():
    from unittest.mock import Mock
    return Mock()

@pytest.mark.parametrize("queue_key, expected", [
    ("test_queue", ["job1", "job2"]),
    (None, []),
    ("empty_queue", [])
])
def test_list_queued_jobs(mock_redis, queue_key, expected):
    jobs = list_queued_jobs(queue_key=queue_key)
    assert jobs == expected

@pytest.mark.parametrize("invalid_input", [123, {}, [], True])
def test_list_queued_jobs_with_invalid_inputs(invalid_input):
    with pytest.raises(TypeError):
        list_queued_jobs(queue_key=invalid_input)

async def test_list_queued_jobs_async(mock_redis):
    from gateway.app.core.jobs import list_queued_jobs
    mock_redis.lrange.return_value = ["job1", "job2"]
    
    jobs = await list_queued_jobs(queue_key="test_queue")
    assert jobs == ["job1", "job2"]