import pytest

class MockThreatModel:
    pass

def test_init_happy_path():
    tm = MockThreatModel()
    inst = Reasoning(tm)
    assert inst.threat_model is tm
    assert inst.logger is not None

def test_init_empty_threat_model():
    inst = Reasoning(None)
    assert inst.threat_model is None
    assert inst.logger is not None

def test_init_none_threat_model():
    inst = Reasoning(None)
    assert inst.threat_model is None
    assert inst.logger is not None

def test_init_boundary_values():
    tm = MockThreatModel()
    for value in [1, 2.5, "string", (), []]:
        inst = Reasoning(value)
        assert inst.threat_model == value
        assert inst.logger is not None