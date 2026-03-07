import pytest
import fcntl
from contextlib import contextmanager

@contextmanager
def file_lock(fp):
    """
    Advisory file locking using fcntl.flock (Linux-only).
    Ensures exclusive access to a file during the life of the context.
    """
    fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)

def test_file_lock_happy_path(tmpdir):
    # Create a temporary file
    filepath = tmpdir.join("testfile.txt")
    with open(filepath, 'w') as fp:
        pass

    with file_lock(fp):
        # Check if the lock is held (expected to pass)
        pass

def test_file_lock_async_behavior(tmpdir):
    import asyncio

    async def acquire_and_release():
        filepath = tmpdir.join("testfile.txt")
        with open(filepath, 'w') as fp:
            pass

        await file_lock(fp)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(acquire_and_release())

def test_file_lock_invalid_input():
    with pytest.raises(TypeError):
        with file_lock(None):
            pass