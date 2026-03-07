# unsloth_compiled_cache/factories.py

from typing import Type

class TrainerFactory:
    @staticmethod
    def get_trainer(trainer_type: str) -> Type['Trainer']:
        if trainer_type == 'BCO':
            from .UnslothBCOTrainer import UnslothBCOTrainer
            return UnslothBCOTrainer
        elif trainer_type == 'Reward':
            from .UnslothRewardTrainer import UnslothRewardTrainer
            return UnslothRewardTrainer
        # Add other trainer types here
        else:
            raise ValueError(f"Unsupported trainer type: {trainer_type}")

# Usage example in a module:
if __name__ == '__main__':
    trainer = TrainerFactory.get_trainer('BCO')
    trainer.train()