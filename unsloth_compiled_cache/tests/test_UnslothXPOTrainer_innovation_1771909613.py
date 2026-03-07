import pytest
import torch

from unsloth_compiled_cache.UnslothXPOTrainer import UnslothXPOTrainer

def test_compute_rewards_happy_path():
    # Create a mock instance of UnslothXPOTrainer
    trainer = UnslothXPOTrainer()

    # Mock reward_funcs, processing_class, and args
    trainer.reward_funcs = lambda x: (None, torch.tensor([1.0, 2.0]), None)
    trainer.processing_class = type('MockProcessingClass', (object,), {'pad_token_id': 0, 'eos_token_id': 2})
    trainer.args = type('MockArgs', (object,), {'missing_eos_penalty': None})

    # Mock model_data and ref_data
    model_data = {
        "input_ids": torch.tensor([[1, 2, 3], [4, 5, 6]])
    }
    ref_data = {
        "input_ids": torch.tensor([[7, 8, 9], [10, 11, 12]])
    }

    # Call the function
    model_scores, ref_scores = trainer._compute_rewards(model_data, ref_data, context_length=3)

    # Assert results
    assert torch.allclose(model_scores, torch.tensor([1.0, 2.0]))
    assert torch.allclose(ref_scores, torch.tensor([1.0, 2.0]))

def test_compute_rewards_empty_input():
    trainer = UnslothXPOTrainer()

    trainer.reward_funcs = lambda x: (None, torch.tensor([]), None)
    trainer.processing_class = type('MockProcessingClass', (object,), {'pad_token_id': 0, 'eos_token_id': 2})
    trainer.args = type('MockArgs', (object,), {'missing_eos_penalty': None})

    model_data = {
        "input_ids": torch.tensor([])
    }
    ref_data = {
        "input_ids": torch.tensor([])
    }

    model_scores, ref_scores = trainer._compute_rewards(model_data, ref_data, context_length=0)

    assert torch.allclose(model_scores, torch.tensor([]))
    assert torch.allclose(ref_scores, torch.tensor([]))

def test_compute_rewards_with_eos_penalty():
    trainer = UnslothXPOTrainer()

    trainer.reward_funcs = lambda x: (None, torch.tensor([1.0, 2.0]), None)
    trainer.processing_class = type('MockProcessingClass', (object,), {'pad_token_id': 0, 'eos_token_id': 2})
    trainer.args = type('MockArgs', (object,), {'missing_eos_penalty': -1.0})

    model_data = {
        "input_ids": torch.tensor([[1, 2, 3], [4, 5, 6]])
    }
    ref_data = {
        "input_ids": torch.tensor([[7, 8, 9], [10, 11, 12]])
    }

    model_scores, ref_scores = trainer._compute_rewards(model_data, ref_data, context_length=3)

    assert torch.allclose(model_scores, torch.tensor([1.0 - 1.0, 2.0 - 1.0]))
    assert torch.allclose(ref_scores, torch.tensor([1.0 - 1.0, 2.0 - 1.0]))

def test_compute_rewards_with_missing_eos_penalty():
    trainer = UnslothXPOTrainer()

    trainer.reward_funcs = lambda x: (None, torch.tensor([1.0, 2.0]), None)
    trainer.processing_class = type('MockProcessingClass', (object,), {'pad_token_id': 0, 'eos_token_id': 2})
    trainer.args = type('MockArgs', (object,), {'missing_eos_penalty': -0.5})

    model_data = {
        "input_ids": torch.tensor([[1, 2], [3, 4]])
    }
    ref_data = {
        "input_ids": torch.tensor([[5, 6], [7, 8]])
    }

    model_scores, ref_scores = trainer._compute_rewards(model_data, ref_data, context_length=2)

    assert torch.allclose(model_scores, torch.tensor([1.0, 2.0]))
    assert torch.allclose(ref_scores, torch.tensor([1.0, 2.0]))