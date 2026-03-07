import pytest
from gateway.app.core.training_harness import TrainingHarness

def test_training_harness_init_happy_path():
    # Test with valid dataset and dataset_path
    test_dataset = "test_dataset"
    test_path = "/path/to/dataset"
    harness = TrainingHarness(test_dataset, test_path)
    
    assert harness.dataset == test_dataset
    assert harness.dataset_path == test_path

def test_training_harness_init_with_none_dataset():
    # Test when dataset is None
    test_path = "/path/to/dataset"
    harness = TrainingHarness(dataset=None, dataset_path=test_path)
    
    assert harness.dataset is None
    assert harness.dataset_path == test_path

def test_training_harness_init_with_none_path():
    # Test when dataset_path is None
    test_dataset = "test_dataset"
    harness = TrainingHarness(dataset=test_dataset, dataset_path=None)
    
    assert harness.dataset == test_dataset
    assert harness.dataset_path is None

def test_training_harness_init_with_all_none():
    # Test when both are None
    harness = TrainingHarness()
    
    assert harness.dataset is None
    assert harness.dataset_path is None