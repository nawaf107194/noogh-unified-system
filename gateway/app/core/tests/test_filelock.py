import pytest
from contextlib import closing
from io import BytesIO
import fcntl
from gateway.app.core.filelock import file_lock

@pytest.fixture
def temp_file():
    with closing(BytesIO()) as fp:
        yield fp

def test_file_lock_happy_path(temp_file):
    with pytest.raises(ValueError) as excinfo:
        with file_lock(None):
            pass
    assert "File descriptor cannot be None" in str(excinfo.value)

def test_file_lock_invalid_input(temp_file):
    with pytest.raises(TypeError) as excinfo:
        with file_lock("not a file"):
            pass
    assert "Expected a file object, got 'str'" in str(excinfo.value)

async def test_file_lock_async_behavior(temp_file):
    async def async_func():
        with file_lock(temp_file):
            await asyncio.sleep(0.1)
    
    loop = asyncio.get_event_loop()
    tasks = [async_func() for _ in range(5)]
    await asyncio.gather(*tasks)