import pytest

from .factories_1772062524 import create_trainer

def test_create_trainer_happy_path():
    assert create_trainer('BCO').__name__ == 'UnslothBCOTrainer'
    assert create_trainer('Reward').__name__ == 'UnslothRewardTrainer'
    assert create_trainer('SFT').__name__ == 'UnslothSFTTrainer'
    assert create_trainer('XPO').__name__ == 'UnslothXPOTrainer'
    assert create_trainer('GKD').__name__ == 'UnslothGKDTrainer'
    assert create_trainer('NashMD').__name__ == 'UnslothNashMDTrainer'
    assert create_trainer('PRM').__name__ == 'UnslothPRMTrainer'
    assert create_trainer('RLOO').__name__ == 'UnslothRLOOTrainer'
    assert create_trainer('OnlineDPO').__name__ == 'UnslothOnlineDPOTrainer'
    assert create_trainer('CPO').__name__ == 'UnslothCPOTrainer'
    assert create_trainer('DPO').__name__ == 'UnslothDPOTrainer'
    assert create_trainer('PPO').__name__ == 'UnslothPPOTrainer'
    assert create_trainer('KTO').__name__ == 'UnslothKTOTrainer'

def test_create_trainer_edge_cases():
    assert create_trainer(None) is None
    assert create_trainer('') is None
    with pytest.raises(ValueError) as exc_info:
        create_trainer('unknown_type')
    assert str(exc_info.value) == "Unknown trainer type: unknown_type"