import pytest

class MockNeuronFabric:
    def __init__(self, source_id, target_id, synapse_id=None):
        self.source_id = source_id
        self.target_id = target_id
        self.synapse_id = synapse_id

    def __post_init__(self):
        if not self.synapse_id:
            self.synapse_id = f"syn_{self.source_id[:8]}_{self.target_id[:8]}"


def test_post_init_happy_path():
    nf = MockNeuronFabric("source12345", "target67890")
    nf.__post_init__()
    assert nf.synapse_id == "syn_source1_target678"


def test_post_init_empty_ids():
    nf = MockNeuronFabric("", "")
    nf.__post_init__()
    assert nf.synapse_id == "syn______"


def test_post_init_none_ids():
    nf = MockNeuronFabric(None, None)
    nf.__post_init__()
    assert nf.synapse_id == "syn_None_Non"


def test_post_init_with_synapse_id():
    nf = MockNeuronFabric("source12345", "target67890", "predefined_synapse_id")
    nf.__post_init__()
    assert nf.synapse_id == "predefined_synapse_id"


def test_post_init_large_input_ids():
    nf = MockNeuronFabric("a"*100, "b"*100)
    nf.__post_init__()
    assert nf.synapse_id == "syn_aaaaaaaaaaabbbbbbbbbbb"


def test_post_init_invalid_input_ids():
    with pytest.raises(TypeError):
        nf = MockNeuronFabric(12345, 67890)  # Passing integers instead of strings
        nf.__post_init__()