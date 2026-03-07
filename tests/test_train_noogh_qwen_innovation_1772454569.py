import pytest
from unittest.mock import patch, MagicMock
from noogh_unified_system.src.train_noogh_qwen import load_dataset

DATASET_PATH = "test_dataset.json"
PROMPT_TEMPLATE = "Type: {type}, Instruction: {instruction}, Input: {input}, Output: {output}, Reasoning: {reasoning}, Confidence: {confidence}"

@pytest.fixture
def mock_open():
    with patch('builtins.open', new_callable=MagicMock) as mock_file:
        yield mock_file

@pytest.fixture
def mock_json_loads():
    with patch('json.loads') as mock_loads:
        yield mock_loads

def test_happy_path(mock_open, mock_json_loads):
    # Mock the dataset file
    mock_open.return_value.__iter__.return_value = [
        '{"type": "test", "instruction": "test instruction", "input": "test input", "output": "test output"}\n',
        '{"type": "another_test", "instruction": "another test instruction", "input": "another test input", "output": "another test output"}\n'
    ]

    # Mock json.loads to return the sample data
    mock_json_loads.side_effect = [
        {"type": "test", "instruction": "test instruction", "input": "test input", "output": "test output"},
        {"type": "another_test", "instruction": "another test instruction", "input": "another test input", "output": "another test output"}
    ]

    # Call the function
    dataset = load_dataset()

    # Assert the number of samples loaded
    assert len(dataset) == 2

    # Assert the formatted text
    expected_texts = [
        'Type: test, Instruction: test instruction, Input: test input, Output: test output, Reasoning: Analysis based on system architecture., Confidence: 0.85',
        'Type: another_test, Instruction: another test instruction, Input: another test input, Output: another test output, Reasoning: Analysis based on system architecture., Confidence: 0.85'
    ]
    actual_texts = [item['text'] for item in dataset]
    assert actual_texts == expected_texts

def test_edge_case_empty_file(mock_open, mock_json_loads):
    # Mock the empty dataset file
    mock_open.return_value.__iter__.return_value = []

    # Call the function
    dataset = load_dataset()

    # Assert no samples are loaded
    assert len(dataset) == 0

def test_edge_case_none_file_path(mock_open):
    # Set DATASET_PATH to None
    global DATASET_PATH
    DATASET_PATH = None

    # Call the function
    with pytest.raises(ValueError, match="DATASET_PATH must be a non-empty string"):
        load_dataset()

    # Reset DATASET_PATH
    DATASET_PATH = "test_dataset.json"

def test_edge_case_empty_line(mock_open, mock_json_loads):
    # Mock the dataset file with an empty line
    mock_open.return_value.__iter__.return_value = [
        '\n',
        '{"type": "test", "instruction": "test instruction", "input": "test input", "output": "test output"}\n'
    ]

    # Mock json.loads to return the sample data
    mock_json_loads.side_effect = [
        {"type": "test", "instruction": "test instruction", "input": "test input", "output": "test output"}
    ]

    # Call the function
    dataset = load_dataset()

    # Assert only one sample is loaded
    assert len(dataset) == 1

def test_error_case_invalid_json(mock_open, mock_json_loads):
    # Mock the dataset file with an invalid JSON line
    mock_open.return_value.__iter__.return_value = [
        '{"type": "test", "instruction": "test instruction", "input": "test input", "output": "test output"\n',
        '{"type": "another_test", "instruction": "another test instruction", "input": "another test input", "output": "another test output"}\n'
    ]

    # Mock json.loads to raise JSONDecodeError
    mock_json_loads.side_effect = [
        json.JSONDecodeError("Expecting property name enclosed in double quotes: line 1 column 76 (char 75)", "", 0),
        {"type": "another_test", "instruction": "another test instruction", "input": "another test input", "output": "another test output"}
    ]

    # Call the function
    dataset = load_dataset()

    # Assert only one sample is loaded due to invalid JSON
    assert len(dataset) == 1