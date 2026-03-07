import pytest
from unittest.mock import patch, mock_open, MagicMock

from train_sovereign_7b import load_dataset, DATASET_PATH, PROMPT_TEMPLATE
from datasets import Dataset

@pytest.fixture
def temp_dataset_file(tmpdir):
    temp_file = tmpdir.join("dataset.jsonl")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write('{"task_type": "test", "instruction": "instr", "output": "out"}\n')
        f.write('{"task_type": "test2", "instruction": "instr2", "output": "out2"}\n')
        f.write('{"category": "unknown", "expected": {"approach": ["step1"], "acceptance_checks": ["check1"]}}\n')
    return temp_file

def test_load_dataset_happy_path(temp_dataset_file):
    with patch.object(DATASET_PATH, 'expanduser', return_value=temp_dataset_file), \
         open(temp_dataset_file, 'r', encoding='utf-8') as f:
        result = load_dataset()
    
    assert isinstance(result, Dataset)
    assert len(result) == 3
    assert result[0]['text'] == PROMPT_TEMPLATE.format(
        task_type='test',
        instruction='instr',
        output='out'
    )
    assert result[1]['text'] == PROMPT_TEMPLATE.format(
        task_type='test2',
        instruction='instr2',
        output='out2'
    )
    assert result[2]['text'] == PROMPT_TEMPLATE.format(
        task_type='unknown',
        instruction='',
        output="الخطوات:\n- step1\nمعايير القبول:\n✓ check1"
    )

def test_load_dataset_empty_file(temp_dataset_file):
    with patch.object(DATASET_PATH, 'expanduser', return_value=temp_dataset_file), \
         mock_open(read_data='') as mock_file:
        with patch('builtins.open', return_value=mock_file) as mock_open_func:
            result = load_dataset()
    
    assert isinstance(result, Dataset)
    assert len(result) == 0

def test_load_dataset_invalid_json(temp_dataset_file):
    with patch.object(DATASET_PATH, 'expanduser', return_value=temp_dataset_file), \
         mock_open(read_data='{"task_type": "test", "instruction": "instr"') as mock_file:
        with patch('builtins.open', return_value=mock_file) as mock_open_func:
            result = load_dataset()
    
    assert isinstance(result, Dataset)
    assert len(result) == 0

def test_load_dataset_missing_fields(temp_dataset_file):
    with patch.object(DATASET_PATH, 'expanduser', return_value=temp_dataset_file), \
         open(temp_dataset_file, 'r', encoding='utf-8') as f:
        result = load_dataset()
    
    assert isinstance(result, Dataset)
    assert len(result) == 3
    assert result[0]['text'] == PROMPT_TEMPLATE.format(
        task_type='test',
        instruction='instr',
        output='out'
    )
    assert result[1]['text'] == PROMPT_TEMPLATE.format(
        task_type='test2',
        instruction='instr2',
        output='out2'
    )
    assert result[2]['text'] == PROMPT_TEMPLATE.format(
        task_type='unknown',
        instruction='',
        output="سأقوم بتحليل المشكلة وتقديم حل مناسب."
    )

def test_load_dataset_no_samples(temp_dataset_file):
    with patch.object(DATASET_PATH, 'expanduser', return_value=temp_dataset_file), \
         mock_open(read_data='\n'.join(['{}', '{}'])) as mock_file:
        with patch('builtins.open', return_value=mock_file) as mock_open_func:
            result = load_dataset()
    
    assert isinstance(result, Dataset)
    assert len(result) == 0