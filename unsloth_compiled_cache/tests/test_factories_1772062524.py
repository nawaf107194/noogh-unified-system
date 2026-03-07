import pytest
from typing import Type

def test_create_trainer_happy_path():
    from .unsloth_compiled_cache.factories_1772062524 import create_trainer
    
    trainer_types = [
        'BCO',
        'Reward',
        'SFT',
        'XPO',
        'GKD',
        'NashMD',
        'PRM',
        'RLOO',
        'OnlineDPO',
        'CPO',
        'DPO',
        'PPO',
        'KTO'
    ]
    
    for trainer_type in trainer_types:
        trainer_class = create_trainer(trainer_type)
        assert isinstance(trainer_class, type)

def test_create_trainer_edge_cases():
    from .unsloth_compiled_cache.factories_1772062524 import create_trainer
    
    edge_cases = [None, '', ' ', 'unknown', 123]
    
    for edge_case in edge_cases:
        trainer_class = create_trainer(edge_case)
        assert trainer_class is None

def test_create_trainer_error_cases():
    from .unsloth_compiled_cache.factories_1772062524 import create_trainer
    
    with pytest.raises(ValueError) as e:
        create_trainer('unknown')
    
    assert str(e.value) == "Unknown trainer type: unknown"