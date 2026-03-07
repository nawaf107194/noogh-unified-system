import pytest
from typing import Iterable, List
import itertools

class DataPipelineOptimizer:
    def batch(self, data: Iterable[T], batch_size: int) -> Iterable[List[T]]:
        """Batch data into chunks of specified size."""
        iterator = iter(data)
        while True:
            chunk = list(itertools.islice(iterator, batch_size))
            if not chunk:
                return
            yield chunk

@pytest.fixture
def optimizer():
    return DataPipelineOptimizer()

def test_batch_happy_path(optimizer):
    data = [1, 2, 3, 4, 5, 6]
    batch_size = 2
    result = list(optimizer.batch(data, batch_size))
    assert result == [[1, 2], [3, 4], [5, 6]]

def test_batch_empty_input(optimizer):
    data: Iterable[int] = []
    batch_size = 2
    result = list(optimizer.batch(data, batch_size))
    assert result == []

def test_batch_none_input(optimizer):
    data = None
    batch_size = 2
    result = optimizer.batch(data, batch_size)
    assert result is None

def test_batch_boundary_batch_size(optimizer):
    data = [1]
    batch_size = 1
    result = list(optimizer.batch(data, batch_size))
    assert result == [[1]]

def test_batch_large_batch_size(optimizer):
    data = [1, 2, 3, 4, 5]
    batch_size = 10
    result = list(optimizer.batch(data, batch_size))
    assert result == [[1, 2, 3, 4, 5]]