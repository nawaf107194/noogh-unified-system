import pytest
import torch
from pytorch_lightning import Trainer
from unsloth_compiled_cache.UnslothORPOTrainer import UnslothORPOTrainer

@pytest.fixture
def trainer():
    return UnslothORPOTrainer(beta=1.0, accelerator=None)

def test_happy_path(trainer):
    batch_size = 5
    policy_chosen_logps = torch.tensor([0.5] * batch_size)
    policy_rejected_logps = torch.tensor([-0.5] * batch_size)
    
    losses, chosen_rewards, rejected_rewards, log_odds_ratio_mean, log_odds_mean = trainer.odds_ratio_loss(
        policy_chosen_logps, policy_rejected_logps
    )
    
    assert isinstance(losses, torch.FloatTensor)
    assert isinstance(chosen_rewards, torch.FloatTensor)
    assert isinstance(rejected_rewards, torch.FloatTensor)
    assert isinstance(log_odds_ratio_mean, torch.FloatTensor)
    assert isinstance(log_odds_mean, torch.FloatTensor)
    
    assert losses.shape == (batch_size,)
    assert chosen_rewards.shape == (batch_size,)
    assert rejected_rewards.shape == (batch_size,)
    
    # Check that the loss is positive
    assert torch.all(losses > 0)

def test_edge_cases(trainer):
    batch_size = 5
    
    # Empty tensors
    policy_chosen_logps_empty = torch.tensor([])
    policy_rejected_logps_empty = torch.tensor([])
    
    losses, chosen_rewards, rejected_rewards, log_odds_ratio_mean, log_odds_mean = trainer.odds_ratio_loss(
        policy_chosen_logps_empty, policy_rejected_logps_empty
    )
    
    assert losses is None
    assert chosen_rewards is None
    assert rejected_rewards is None
    assert log_odds_ratio_mean is None
    assert log_odds_mean is None
    
    # None inputs
    policy_chosen_logps_none = None
    policy_rejected_logps_none = None
    
    losses, chosen_rewards, rejected_rewards, log_odds_ratio_mean, log_odds_mean = trainer.odds_ratio_loss(
        policy_chosen_logps_none, policy_rejected_logps_none
    )
    
    assert losses is None
    assert chosen_rewards is None
    assert rejected_rewards is None
    assert log_odds_ratio_mean is None
    assert log_odds_mean is None
    
    # Boundary values
    policy_chosen_logps_boundary = torch.tensor([0.0] * batch_size)
    policy_rejected_logps_boundary = torch.tensor([-1e-6] * batch_size)
    
    losses, chosen_rewards, rejected_rewards, log_odds_ratio_mean, log_odds_mean = trainer.odds_ratio_loss(
        policy_chosen_logps_boundary, policy_rejected_logps_boundary
    )
    
    assert isinstance(losses, torch.FloatTensor)
    assert isinstance(chosen_rewards, torch.FloatTensor)
    assert isinstance(rejected_rewards, torch.FloatTensor)
    assert isinstance(log_odds_ratio_mean, torch.FloatTensor)
    assert isinstance(log_odds_mean, torch.FloatTensor)
    
    assert losses.shape == (batch_size,)
    assert chosen_rewards.shape == (batch_size,)
    assert rejected_rewards.shape == (batch_size,)

def test_error_cases(trainer):
    batch_size = 5
    
    # Invalid input types
    policy_chosen_logps_invalid_type = "not a tensor"
    policy_rejected_logps_invalid_type = "not a tensor"
    
    with pytest.raises(TypeError):
        losses, chosen_rewards, rejected_rewards, log_odds_ratio_mean, log_odds_mean = trainer.odds_ratio_loss(
            policy_chosen_logps_invalid_type, policy_rejected_logps_invalid_type
        )