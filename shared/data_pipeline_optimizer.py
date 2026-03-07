import itertools
from typing import List, Callable, TypeVar, Iterable

T = TypeVar('T')

class DataPipelineOptimizer:
    def __init__(self):
        self.transformations = []

    def batch(self, data: Iterable[T], batch_size: int) -> Iterable[List[T]]:
        """Batch data into chunks of specified size."""
        iterator = iter(data)
        while True:
            chunk = list(itertools.islice(iterator, batch_size))
            if not chunk:
                return
            yield chunk

    def filter(self, predicate: Callable[[T], bool]) -> None:
        """Add a filter predicate to the pipeline."""
        self.transformations.append(lambda x: filter(predicate, x))

    def map(self, func: Callable[[T], T]) -> None:
        """Add a mapping function to the pipeline."""
        self.transformations.append(lambda x: map(func, x))

    def process(self, data: Iterable[T]) -> Iterable[T]:
        """Apply all transformations in sequence to the data."""
        for transform in self.transformations:
            data = transform(data)
        return data

# Example usage
if __name__ == "__main__":
    optimizer = DataPipelineOptimizer()
    optimizer.filter(lambda x: x > 10)
    optimizer.map(lambda x: x * 2)

    data = range(20)
    processed_data = optimizer.process(data)
    print(list(processed_data))  # Output: [22, 24, 26, 28, 30, 32, 34, 36, 38, 40]