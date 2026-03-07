import pytest

from shared.data_pipeline_optimizer import DataPipelineOptimizer, Transform

def double(x):
    return x * 2

def add_one(x):
    return x + 1

class TestDataPipelineOptimizer:

    @pytest.fixture
    def optimizer(self):
        transform1 = Transform(double)
        transform2 = Transform(add_one)
        return DataPipelineOptimizer([transform1, transform2])

    def test_happy_path(self, optimizer):
        data = [1, 2, 3]
        result = list(optimizer.process(data))
        assert result == [3, 5, 7]

    def test_empty_input(self, optimizer):
        data = []
        result = list(optimizer.process(data))
        assert result == []

    def test_none_input(self, optimizer):
        data = None
        result = optimizer.process(data)
        assert result is None

    def test_boundary_values(self, optimizer):
        data = [0, -1, 1]
        result = list(optimizer.process(data))
        assert result == [1, 0, 3]

    def test_invalid_input_type(self, optimizer):
        data = "not iterable"
        result = optimizer.process(data)
        assert result is None