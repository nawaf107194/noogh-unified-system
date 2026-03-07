# unsloth_compiled_cache/factories.py

from typing import Type

class TrainerFactory:
    @staticmethod
    def create_trainer(trainer_type: str) -> Type:
        if trainer_type == 'BCO':
            from .UnslothBCOTrainer import UnslothBCOTrainer
            return UnslothBCOTrainer
        elif trainer_type == 'Reward':
            from .UnslothRewardTrainer import UnslothRewardTrainer
            return UnslothRewardTrainer
        elif trainer_type == 'SFT':
            from .UnslothSFTTrainer import UnslothSFTTrainer
            return UnslothSFTTrainer
        elif trainer_type == 'XPO':
            from .UnslothXPOTrainer import UnslothXPOTrainer
            return UnslothXPOTrainer
        elif trainer_type == 'GKD':
            from .UnslothGKDTrainer import UnslothGKDTrainer
            return UnslothGKDTrainer
        elif trainer_type == 'NashMD':
            from .UnslothNashMDTrainer import UnslothNashMDTrainer
            return UnslothNashMDTrainer
        elif trainer_type == 'PRM':
            from .UnslothPRMTrainer import UnslothPRMTrainer
            return UnslothPRMTrainer
        elif trainer_type == 'RLOO':
            from .UnslothRLOOTrainer import UnslothRLOOTrainer
            return UnslothRLOOTrainer
        elif trainer_type == 'OnlineDPO':
            from .UnslothOnlineDPOTrainer import UnslothOnlineDPOTrainer
            return UnslothOnlineDPOTrainer
        elif trainer_type == 'CPO':
            from .UnslothCPOTrainer import UnslothCPOTrainer
            return UnslothCPOTrainer
        elif trainer_type == 'DPO':
            from .UnslothDPOTrainer import UnslothDPOTrainer
            return UnslothDPOTrainer
        elif trainer_type == 'PPO':
            from .UnslothPPOTrainer import UnslothPPOTrainer
            return UnslothPPOTrainer
        elif trainer_type == 'KTO':
            from .UnslothKTOTrainer import UnslothKTOTrainer
            return UnslothKTOTrainer
        else:
            raise ValueError(f"Unknown trainer type: {trainer_type}")