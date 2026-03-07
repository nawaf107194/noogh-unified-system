import pytest
from unittest.mock import patch, MagicMock
from auto_gguf import merge_lora
import subprocess
import logging

# Mock logger
logger = logging.getLogger(__name__)

# Mock paths and models
BASE_MODEL = "mock_base_model"
LORA_ADAPTER = "mock_lora_adapter"
OUTPUT_DIR = "/tmp/merged_model"

# Mocking dependencies
@patch('transformers.AutoModelForCausalLM')
@patch('transformers.AutoTokenizer')
@patch('peft.PeftModel')
@patch('subprocess.run')
@patch('logging.Logger')
def test_merge_lora_happy_path(mock_logger, mock_subprocess_run, mock_peft_model, mock_auto_tokenizer, mock_auto_model_for_causal_lm):
    # Setup mocks
    mock_logger.return_value = logger
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    
    # Call function
    result = merge_lora(BASE_MODEL, LORA_ADAPTER, OUTPUT_DIR)
    
    # Assertions
    assert result["success"] == True
    assert result["merged_dir"] == OUTPUT_DIR
    mock_auto_model_for_causal_lm.from_pretrained.assert_called_once_with(BASE_MODEL, torch_dtype="auto", device_map="cpu")
    mock_peft_model.from_pretrained.assert_called_once()

@patch('transformers.AutoModelForCausalLM')
@patch('transformers.AutoTokenizer')
@patch('peft.PeftModel')
@patch('subprocess.run')
@patch('logging.Logger')
def test_merge_lora_edge_cases(mock_logger, mock_subprocess_run, mock_peft_model, mock_auto_tokenizer, mock_auto_model_for_causal_lm):
    # Test with None output dir
    result = merge_lora(BASE_MODEL, LORA_ADAPTER, None)
    assert result["success"] == True
    
    # Test with empty strings
    result = merge_lora("", "", "")
    assert result["success"] == True

@patch('transformers.AutoModelForCausalLM')
@patch('transformers.AutoTokenizer')
@patch('peft.PeftModel')
@patch('subprocess.run')
@patch('logging.Logger')
def test_merge_lora_error_cases(mock_logger, mock_subprocess_run, mock_peft_model, mock_auto_tokenizer, mock_auto_model_for_causal_lm):
    # Test with invalid base model
    with pytest.raises(Exception):
        merge_lora(None, LORA_ADAPTER, OUTPUT_DIR)
    
    # Test with invalid LoRA adapter
    with pytest.raises(Exception):
        merge_lora(BASE_MODEL, None, OUTPUT_DIR)

@patch('transformers.AutoModelForCausalLM')
@patch('transformers.AutoTokenizer')
@patch('peft.PeftModel')
@patch('subprocess.run')
@patch('logging.Logger')
def test_merge_lora_cli_fallback(mock_logger, mock_subprocess_run, mock_peft_model, mock_auto_tokenizer, mock_auto_model_for_causal_lm):
    # Simulate ImportError
    mock_auto_model_for_causal_lm.side_effect = ImportError("Mocked ImportError")
    
    # Call function
    result = merge_lora(BASE_MODEL, LORA_ADAPTER, OUTPUT_DIR)
    
    # Assertions
    assert result["success"] == True
    assert result["merged_dir"] == OUTPUT_DIR
    mock_subprocess_run.assert_called_once()

@patch('transformers.AutoModelForCausalLM')
@patch('transformers.AutoTokenizer')
@patch('peft.PeftModel')
@patch('subprocess.run')
@patch('logging.Logger')
def test_merge_lora_cli_fallback_failure(mock_logger, mock_subprocess_run, mock_peft_model, mock_auto_tokenizer, mock_auto_model_for_causal_lm):
    # Simulate ImportError and subprocess failure
    mock_auto_model_for_causal_lm.side_effect = ImportError("Mocked ImportError")
    mock_subprocess_run.return_value = MagicMock(returncode=1)
    
    # Call function
    result = merge_lora(BASE_MODEL, LORA_ADAPTER, OUTPUT_DIR)
    
    # Assertions
    assert result["success"] == False
    assert "error" in result
    mock_subprocess_run.assert_called_once()