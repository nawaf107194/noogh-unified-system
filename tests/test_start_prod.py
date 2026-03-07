import pytest
from unittest.mock import patch, MagicMock
from your_module import live_validation, REDIS_URL

@pytest.fixture(autouse=True)
def mock_redis():
    with patch('redis.from_url') as mock_redis_from_url:
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        yield mock_redis_client

@patch('your_module.time.sleep')
def test_live_validation_happy_path(mock_sleep):
    # Mock Redis operations to simulate successful job submission and processing
    mock_redis().ping.return_value = True
    mock_redis().get.return_value = None  # No initial data for the job
    mock_redis().set.return_value = True
    mock_redis().rpush.return_value = True

    live_validation()

    assert mock_sleep.call_count == 1
    assert mock_redis().get.called_once_with('jobs:data:bad-job-1')
    assert mock_redis().pexpire.called_once_with('jobs:data:bad-job-1', your_module.REDIS_JOB_EXPIRE)

@patch('your_module.time.sleep')
def test_live_validation_empty_payload(mock_sleep):
    # Mock Redis operations for an empty payload
    mock_redis().ping.return_value = True
    mock_redis().get.return_value = None  # No initial data for the job
    mock_redis().set.return_value = True
    mock_redis().rpush.return_value = True

    with patch('json.dumps') as mock_json_dumps:
        mock_json_dumps.side_effect = ValueError("Empty payload")
        live_validation()

    assert mock_sleep.call_count == 1
    assert mock_redis().get.called_once_with('jobs:data:bad-job-1')
    assert not mock_redis().pexpire.called

@patch('your_module.time.sleep')
def test_live_validation_invalid_signature(mock_sleep):
    # Mock Redis operations for an invalid signature
    mock_redis().ping.return_value = True
    mock_redis().get.return_value = None  # No initial data for the job
    mock_redis().set.return_value = True
    mock_redis().rpush.return_value = True

    live_validation()

    assert mock_sleep.call_count == 1
    assert mock_redis().get.called_once_with('jobs:data:bad-job-1')
    assert mock_redis().pexpire.called_once_with('jobs:data:bad-job-1', your_module.REDIS_JOB_EXPIRE)

@patch('your_module.time.sleep')
def test_live_validation_redis_connection_failure(mock_sleep):
    # Mock Redis connection failure
    with patch('redis.from_url') as mock_redis_from_url:
        mock_redis_from_url.side_effect = Exception("Cannot connect to Redis")
        
        live_validation()

    assert not mock_sleep.called
    assert not mock_redis().ping.called
    assert logger.warning.call_count == 1

@patch('your_module.time.sleep')
def test_live_validation_worker_failure(mock_sleep):
    # Mock worker failure (job not rejected)
    mock_redis().ping.return_value = True
    mock_redis().get.return_value = None  # No initial data for the job
    mock_redis().set.return_value = True
    mock_redis().rpush.return_value = True

    with patch('your_module.sys.exit') as mock_sys_exit:
        live_validation()

    assert mock_sleep.call_count == 1
    assert mock_redis().get.called_once_with('jobs:data:bad-job-1')
    assert not mock_redis().pexpire.called
    assert mock_sys_exit.call_args[0] == (1,)