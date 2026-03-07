import pytest
from unified_core.evolution.innovation_applier import InnovationApplier, InnovationStorage

@pytest.fixture
def innovation_applier():
    return InnovationApplier()

def test_init_happy_path(innovation_applier):
    assert isinstance(innovation_applier.storage, InnovationStorage)
    assert isinstance(innovation_applier._applied_innovations, set)
    assert len(innovation_applier._applied_innovations) == 0

def test_init_edge_case_none_pb_file():
    applier = InnovationApplier(pb_file=None)
    assert isinstance(applier.storage, InnovationStorage)
    assert isinstance(applier._applied_innovations, set)
    assert len(applier._applied_innovations) == 0

def test_init_edge_case_empty_pb_file():
    applier = InnovationApplier(pb_file="")
    assert isinstance(applier.storage, InnovationStorage)
    assert isinstance(applier._applied_innovations, set)
    assert len(applier._applied_innovations) == 0

def test_load_applied_history_not_implemented(innovation_applier):
    with pytest.raises(NotImplementedError):
        innovation_applier._load_applied_history()