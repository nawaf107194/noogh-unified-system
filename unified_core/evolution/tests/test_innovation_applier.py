import pytest
from collections import Counter
from unified_core.evolution.innovation_applier import InnovationApplier
from unified_core.learning_pb2 import Innovation

@pytest.fixture
def innovation_applier():
    return InnovationApplier()

def create_innovation(type_name, priority=1, suggested_at=None):
    innovation = Innovation()
    innovation.context['original_type'] = type_name
    innovation.priority = priority
    if suggested_at:
        innovation.suggested_at.CopyFrom(suggested_at)
    return innovation

@pytest.mark.parametrize("innovations, expected", [
    ([], []),
    ([create_innovation('A', 1)], [create_innovation('A', 1)]),
    ([create_innovation('A', 2), create_innovation('B', 1)], [create_innovation('A', 2), create_innovation('B', 1)]),
    ([create_innovation('A', 1, suggested_at=10), create_innovation('A', 1, suggested_at=5)], [create_innovation('A', 1, suggested_at=10), create_innovation('A', 1, suggested_at=5)]),
    ([create_innovation('A', 2), create_innovation('B', 2), create_innovation('A', 1)], [create_innovation('A', 2), create_innovation('B', 2), create_innovation('A', 1)]),
    ([create_innovation('A', 1, suggested_at=10), create_innovation('A', 1, suggested_at=5), create_innovation('A', 2)], [create_innovation('A', 2), create_innovation('A', 1, suggested_at=10), create_innovation('A', 1, suggested_at=5)]),
])
def test_prioritize_innovations_happy_path(innovation_applier, innovations, expected):
    result = innovation_applier.prioritize_innovations(innovations)
    assert result == expected