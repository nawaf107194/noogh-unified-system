import pytest
import torch

def calculate_pad_tokens_in_prompt(
    input_ids: torch.Tensor,
    logits_to_keep: int,
    pad_token_id: int
) -> torch.Tensor:
    """
    Given prompt tensor, it returns all the left padded tokens in that sequence. so [pad, pad, pad, cat] = 3 tokens
    """
    if logits_to_keep >= input_ids.shape[1]:
        raise ValueError("logits_to_keep must be smaller than the sequence length.")

    prompt_section = input_ids[:, :-logits_to_keep]

    padding_mask = (prompt_section == pad_token_id)

    pad_token_counts = padding_mask.sum(dim=1)

    return pad_token_counts

# Test cases
def test_calculate_pad_tokens_in_prompt_happy_path():
    input_ids = torch.tensor([[2, 3, 4, 0], [5, 6, 7, 8]])
    logits_to_keep = 1
    pad_token_id = 0
    expected_output = torch.tensor([3, 0])
    assert torch.equal(calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id), expected_output)

def test_calculate_pad_tokens_in_prompt_edge_case_empty_input():
    input_ids = torch.tensor([])
    logits_to_keep = 0
    pad_token_id = 0
    expected_output = torch.tensor([])
    assert torch.equal(calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id), expected_output)

def test_calculate_pad_tokens_in_prompt_edge_case_all_padded():
    input_ids = torch.tensor([[0, 0, 0], [0, 0, 0]])
    logits_to_keep = 2
    pad_token_id = 0
    expected_output = torch.tensor([3, 3])
    assert torch.equal(calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id), expected_output)

def test_calculate_pad_tokens_in_prompt_edge_case_all_non_padded():
    input_ids = torch.tensor([[1, 2, 3], [4, 5, 6]])
    logits_to_keep = 0
    pad_token_id = 0
    expected_output = torch.tensor([0, 0])
    assert torch.equal(calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id), expected_output)

def test_calculate_pad_tokens_in_prompt_error_case_invalid_logits_to_keep():
    input_ids = torch.tensor([[2, 3, 4], [5, 6, 7]])
    logits_to_keep = 3
    pad_token_id = 0
    with pytest.raises(ValueError) as exc_info:
        calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id)
    assert str(exc_info.value) == "logits_to_keep must be smaller than the sequence length."

def test_calculate_pad_tokens_in_prompt_error_case_negative_logits_to_keep():
    input_ids = torch.tensor([[2, 3, 4], [5, 6, 7]])
    logits_to_keep = -1
    pad_token_id = 0
    with pytest.raises(ValueError) as exc_info:
        calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id)
    assert str(exc_info.value) == "logits_to_keep must be smaller than the sequence length."

def test_calculate_pad_tokens_in_prompt_error_case_none_input():
    input_ids = None
    logits_to_keep = 1
    pad_token_id = 0
    with pytest.raises(TypeError):
        calculate_pad_tokens_in_prompt(input_ids, logits_to_keep, pad_token_id)