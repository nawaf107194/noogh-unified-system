import pytest
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import numpy as np
import torch

class MockDataset(Dataset):
    def __len__(self):
        return 1000
    
    def __getitem__(self, idx):
        return {
            "embedding_input_ids": torch.randn(32),
            "embedding_attention_mask": torch.ones(32)
        }

class MockTrainer:
    def __init__(self):
        self.args = type('Args', (), {'per_device_train_batch_size': 64, 'dataloader_num_workers': 0, 'dataloader_pin_memory': False})
        self.data_collator = lambda x: x
        self.accelerator = MockAccelerator()
    
    def _vectorize_prompt(self, input_ids, attention_mask):
        return torch.randn(len(input_ids), 128)

class MockAccelerator:
    @staticmethod
    def prepare(data_loader):
        return data_loader
    
    @staticmethod
    def gather_for_metrics(embeddings):
        return embeddings

@pytest.fixture
def trainer():
    return MockTrainer()

def test_get_sample_prompt_embeddings_happy_path(trainer):
    dataset = MockDataset()
    embeddings = trainer._get_sample_prompt_embeddings(dataset)
    assert isinstance(embeddings, torch.FloatTensor)
    assert embeddings.shape == (512, 128)

def test_get_sample_prompt_embeddings_empty_dataset(trainer):
    dataset = MockDataset()
    dataset.__len__ = lambda: 0
    embeddings = trainer._get_sample_prompt_embeddings(dataset)
    assert isinstance(embeddings, torch.FloatTensor)
    assert embeddings.shape == (0, 128)

def test_get_sample_prompt_embeddings_boundary_case(trainer):
    dataset = MockDataset()
    dataset.__len__ = lambda: 10
    embeddings = trainer._get_sample_prompt_embeddings(dataset)
    assert isinstance(embeddings, torch.FloatTensor)
    assert embeddings.shape == (10, 128)

def test_get_sample_prompt_embeddings_invalid_input_dataset_none(trainer):
    with pytest.raises(ValueError) as exc_info:
        trainer._get_sample_prompt_embeddings(None)
    assert str(exc_info.value) == "dataset must be a non-empty Dataset instance"

def test_get_sample_prompt_embeddings_invalid_input_sample_size_negative(trainer):
    dataset = MockDataset()
    with pytest.raises(ValueError) as exc_info:
        trainer._get_sample_prompt_embeddings(dataset, sample_size=-1)
    assert str(exc_info.value) == "sample_size must be a positive integer"