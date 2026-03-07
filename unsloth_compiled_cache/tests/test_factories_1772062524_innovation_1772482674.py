import pytest

from unsloth_compiled_cache.factories_1772062524 import create_trainer

def test_create_trainer_happy_path():
    assert issubclass(create_trainer('BCO'), object)
    assert issubclass(create_trainer('Reward'), object)
    assert issubclass(create_trainer('SFT'), object)
    assert issubclass(create_trainer('XPO'), object)
    assert issubclass(create_trainer('GKD'), object)
    assert issubclass(create_trainer('NashMD'), object)
    assert issubclass(create_trainer('PRM'), object)
    assert issubclass(create_trainer('RLOO'), object)
    assert issubclass(create_trainer('OnlineDPO'), object)
    assert issubclass(create_trainer('CPO'), object)
    assert issubclass(create_trainer('DPO'), object)
    assert issubclass(create_trainer('PPO'), object)
    assert issubclass(create_trainer('KTO'), object)

def test_create_trainer_edge_cases():
    assert create_trainer(None) is None
    assert create_trainer('') is None

def test_create_trainer_error_cases():
    with pytest.raises(ValueError):
        create_trainer('UnknownType')