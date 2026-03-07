import pytest
import fcntl
from unittest.mock import patch

def mock_flock(*args, **kwargs):
    return None

@pytest.mark.parametrize("fp", [
    (open("/tmp/testfile.lock", "w")),
    (None),
    (""),
])
def test_file_lock_with_invalid_inputs(fp):
    with pytest.raises(ValueError):
        with file_lock(fp) as f:
            pass

@patch('fcntl.flock', side_effect=mock_flock)
def test_file_lock_happy_path(mock_flock):
    fp = open("/tmp/testfile.lock", "w")
    with file_lock(fp) as f:
        assert mock_flock.call_args_list == [
            ((fp.fileno(), fcntl.LOCK_EX), {}),
            ((fp.fileno(), fcntl.LOCK_UN), {})
        ]
    fp.close()

@patch('fcntl.flock', side_effect=mock_flock)
async def test_file_lock_async(mock_flock):
    import asyncio
    async def run_test():
        fp = open("/tmp/testfile.lock", "w")
        with file_lock(fp) as f:
            mock_flock.assert_called_once_with(fp.fileno(), fcntl.LOCK_EX)
            await asyncio.sleep(0.1)
            mock_flock.assert_called_with(fp.fileno(), fcntl.LOCK_UN)
        fp.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_test())