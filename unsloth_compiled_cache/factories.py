# unsloth_compiled_cache/factories.py

class TrainerFactory:
    @staticmethod
    def create_trainer(trainer_type, *args, **kwargs):
        if trainer_type == 'BCO':
            from .UnslothBCOTrainer import UnslothBCOTrainer
            return UnslothBCOTrainer(*args, **kwargs)
        elif trainer_type == 'Reward':
            from .UnslothRewardTrainer import UnslothRewardTrainer
            return UnslothRewardTrainer(*args, **kwargs)
        elif trainer_type == 'SFT':
            from .UnslothSFTTrainer import UnslothSFTTrainer
            return UnslothSFTTrainer(*args, **kwargs)
        elif trainer_type == 'XPO':
            from .UnslothXPOTrainer import UnslothXPOTrainer
            return UnslothXPOTrainer(*args, **kwargs)
        elif trainer_type == 'GKD':
            from .UnslothGKDTrainer import UnslothGKDTrainer
            return UnslothGKDTrainer(*args, **kwargs)
        elif trainer_type == 'NashMD':
            from .UnslothNashMDTrainer import UnslothNashMDTrainer
            return UnslothNashMDTrainer(*args, **kwargs)
        elif trainer_type == 'PRM':
            from .UnslothPRMTrainer import UnslothPRMTrainer
            return UnslothPRMTrainer(*args, **kwargs)
        elif trainer_type == 'RLOO':
            from .UnslothRLOOTrainer import UnslothRLOOTrainer
            return UnslothRLOOTrainer(*args, **kwargs)
        elif trainer_type == 'OnlineDPO':
            from .UnslothOnlineDPOTrainer import UnslothOnlineDPOTrainer
            return UnslothOnlineDPOTrainer(*args, **kwargs)
        elif trainer_type == 'CPO':
            from .UnslothCPOTrainer import UnslothCPOTrainer
            return UnslothCPOTrainer(*args, **kwargs)
        elif trainer_type == 'DPO':
            from .UnslothDPOTrainer import UnslothDPOTrainer
            return UnslothDPOTrainer(*args, **kwargs)
        elif trainer_type == 'PPO':
            from .UnslothPPOTrainer import UnslothPPOTrainer
            return UnslothPPOTrainer(*args, **kwargs)
        elif trainer_type == 'KTO':
            from .UnslothKTOTrainer import UnslothKTOTrainer
            return UnslothKTOTrainer(*args, **kwargs)
        elif trainer_type == 'GRPO':
            from .UnslothGRPOTrainer import UnslothGRPOTrainer
            return UnslothGRPOTrainer(*args, **kwargs)
        elif trainer_type == 'ORPO':
            from .UnslothORPOTrainer import UnslothORPOTrainer
            return UnslothORPOTrainer(*args, **kwargs)
        else:
            raise ValueError(f"Unknown trainer type: {trainer_type}")