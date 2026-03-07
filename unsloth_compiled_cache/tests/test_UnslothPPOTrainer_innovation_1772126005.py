import pytest
import torch

from unsloth_compiled_cache.UnslothPPOTrainer import calculate_pad_tokens_in_prompt

def test_calculate_pad_tokens_in_prompt_happy_path():
    input_ids = torch.tensor([[2, 3, 4, 5], [1, 2, 3, 4]])
    logits_to_keep = 2
    pad_token_id = 0
    expected_output = torch.tensor([2, 1])

    output = calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id)
    
    assert torch.equal(output, expected_output)

def test_calculate_pad_tokens_in_prompt_edge_case_empty_input():
    input_ids = torch.empty((0, 4), dtype=torch.long)
    logits_to_keep = 2
    pad_token_id = 0
    expected_output = torch.tensor([])

    output = calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id)
    
    assert torch.equal(output, expected_output)

def test_calculate_pad_tokens_in_prompt_edge_case_none_input():
    with pytest.raises(TypeError):
        calculate_pad_tokens_in_prompt(None, 2, 0)

def test_calculate_pad_tokens_in_prompt_edge_case_zero_logits_to_keep():
    input_ids = torch.tensor([[2, 3, 4, 5], [1, 2, 3, 4]])
    logits_to_keep = 0
    pad_token_id = 0
    expected_output = torch.tensor([0, 0])

    output = calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id)
    
    assert torch.equal(output, expected_output)

def test_calculate_pad_tokens_in_prompt_edge_case_max_logits_to_keep():
    input_ids = torch.tensor([[2, 3, 4, 5], [1, 2, 3, 4]])
    logits_to_keep = 3
    pad_token_id = 0
    expected_output = torch.tensor([1, 1])

    output = calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id)
    
    assert torch.equal(output, expected_output)

def test_calculate_pad_tokens_in_prompt_error_case_invalid_logits_to_keep():
    input_ids = torch.tensor([[2, 3, 4, 5], [1, 2, 3, 4]])
    logits_to_keep = 5
    pad_token_id = 0

    with pytest.raises(ValueError):
        calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id)