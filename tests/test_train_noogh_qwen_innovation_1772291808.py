import pytest
from unittest.mock import patch, MagicMock
from noogh_unified_system.src.train_noogh_qwen import load_dataset

DATASET_PATH = "path/to/dataset.json"
PROMPT_TEMPLATE = "Type: {type}, Instruction: {instruction}, Input: {input}, Output: {output}, Reasoning: {reasoning}, Confidence: {confidence}"

def test_load_dataset_happy_path():
    with patch("builtins.open", MagicMock(side_effect=[IOError, open])):
        # Mocking file read
        mock_file = MagicMock()
        mock_file.__iter__.return_value = [
            '{"type": "task1", "instruction": "inst1", "input": "inp1", "output": "out1"}',
            '{"type": "task2", "instruction": "inst2", "input": "inp2", "output": "out2"}'
        ]
        open.return_value.__enter__.return_value = mock_file
        
        # Mocking Dataset.from_list
        mock_dataset = MagicMock()
        from noogh_unified_system.src.train_noogh_qwen import Dataset
        Dataset.from_list = MagicMock(return_value=mock_dataset)
        
        result = load_dataset()
        assert result == mock_dataset
        open.assert_called_once_with(DATASET_PATH, 'r', encoding='utf-8')
        assert len(result) == 2

def test_load_dataset_empty_file():
    with patch("builtins.open", MagicMock(side_effect=[IOError, open])):
        mock_file = MagicMock()
        mock_file.__iter__.return_value = []
        open.return_value.__enter__.return_value = mock_file
        
        from noogh_unified_system.src.train_noogh_qwen import Dataset
        Dataset.from_list = MagicMock(return_value=MagicMock())
        
        result = load_dataset()
        assert len(result) == 0

def test_load_dataset_invalid_json():
    with patch("builtins.open", MagicMock(side_effect=[IOError, open])):
        mock_file = MagicMock()
        mock_file.__iter__.return_value = [
            '{"type": "task1", "instruction": "inst1", "input": "inp1", "output": "out1"',
            '{"type": "task2", "instruction": "inst2", "input": "inp2", "output": "out2"}'
        ]
        open.return_value.__enter__.return_value = mock_file
        
        from noogh_unified_system.src.train_noogh_qwen import Dataset
        Dataset.from_list = MagicMock(return_value=MagicMock())
        
        result = load_dataset()
        assert len(result) == 1

def test_load_dataset_none_input():
    with patch("builtins.open", MagicMock(side_effect=[IOError, open])):
        mock_file = MagicMock()
        mock_file.__iter__.return_value = [None]
        open.return_value.__enter__.return_value = mock_file
        
        from noogh_unified_system.src.train_noogh_qwen import Dataset
        Dataset.from_list = MagicMock(return_value=MagicMock())
        
        result = load_dataset()
        assert len(result) == 0

def test_load_dataset_error_case():
    with patch("builtins.open", MagicMock(side_effect=[IOError, open])):
        mock_file = MagicMock()
        mock_file.__iter__.return_value = [
            '{"type": "task1", "instruction": "inst1", "input": "inp1", "output": "out1"}',
            'invalid_json_string'
        ]
        open.return_value.__enter__.return_value = mock_file
        
        from noogh_unified_system.src.train_noogh_qwen import Dataset
        Dataset.from_list = MagicMock(return_value=MagicMock())
        
        result = load_dataset()
        assert len(result) == 1