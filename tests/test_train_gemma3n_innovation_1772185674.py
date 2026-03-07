import pytest
from unittest.mock import patch, MagicMock
from noogh_unified_system.src.train_gemma3n import load_and_score_dataset
import json

# Mock constants and dependencies
DATASET_PATH = 'mock_dataset_path'
MAX_SAMPLES = 10

def mock_load_dataset():
    return [
        {
            "messages": [
                {"role": "assistant", "content": "This is an assistant response."},
                {"role": "user", "content": "User input"}
            ],
            "category": "test_category"
        }
    ]

def mock_reward_scorer_compute_reward(text, category):
    return 0.8

def test_load_and_score_dataset_happy_path(mocker):
    # Mock dependencies
    mocker.patch('noogh_unified_system.src.train_gemma3n.load_dataset', return_value=mock_load_dataset())
    mocker.patch('noogh_unified_system.src.train_gemma3n.RewardScorer.compute_reward', side_effect=mock_reward_scorer_compute_reward)
    mocker.patch('noogh_unified_system.src.train_gemma3n.logger')
    
    # Call the function
    result = load_and_score_dataset(MagicMock())
    
    # Assertions
    assert len(result) == 1
    assert 'text' in result[0]
    assert 'reward' in result[0]
    assert 'category' in result[0]

def test_load_and_score_dataset_empty_dataset(mocker):
    # Mock dependencies
    mocker.patch('noogh_unified_system.src.train_gemma3n.load_dataset', return_value=[])
    mocker.patch('noogh_unified_system.src.train_gemma3n.logger')
    
    # Call the function
    result = load_and_score_dataset(MagicMock())
    
    # Assertions
    assert len(result) == 0

def test_load_and_score_dataset_none_dataset(mocker):
    # Mock dependencies
    mocker.patch('noogh_unified_system.src.train_gemma3n.load_dataset', return_value=None)
    mocker.patch('noogh_unified_system.src.train_gemma3n.logger')
    
    # Call the function
    result = load_and_score_dataset(MagicMock())
    
    # Assertions
    assert len(result) == 0

def test_load_and_score_dataset_invalid_messages(mocker):
    # Mock dependencies
    mocker.patch('noogh_unified_system.src.train_gemma3n.load_dataset', return_value=[{"messages": []}])
    mocker.patch('noogh_unified_system.src.train_gemma3n.logger')
    
    # Call the function
    result = load_and_score_dataset(MagicMock())
    
    # Assertions
    assert len(result) == 0

def test_load_and_score_dataset_invalid_assistant_response(mocker):
    # Mock dependencies
    mocker.patch('noogh_unified_system.src.train_gemma3n.load_dataset', return_value=[{"messages": [{"role": "user", "content": "User input"}]}])
    mocker.patch('noogh_unified_system.src.train_gemma3n.logger')
    
    # Call the function
    result = load_and_score_dataset(MagicMock())
    
    # Assertions
    assert len(result) == 0

def test_load_and_score_dataset_tokenizer_failure(mocker):
    # Mock dependencies
    mocker.patch('noogh_unified_system.src.train_gemma3n.load_dataset', return_value=[{"messages": [{"role": "assistant", "content": "This is an assistant response."}, {"role": "user", "content": "User input"}]}])
    mocker.patch('noogh_unified_system.src.train_gemma3n.RewardScorer.compute_reward', side_effect=mock_reward_scorer_compute_reward)
    mocker.patch('noogh_unified_system.src.train_gemma3n.logger')
    
    # Mock tokenizer failure
    with patch.object(MagicMock(), 'apply_chat_template', side_effect=Exception()):
        result = load_and_score_dataset(MagicMock())
    
    # Assertions
    assert len(result) == 1
    assert 'text' in result[0]
    assert '<start_of_turn>user\n[System: User input]' in result[0]['text']