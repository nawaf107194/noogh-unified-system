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
