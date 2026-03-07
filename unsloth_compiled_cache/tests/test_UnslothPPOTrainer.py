import pytest
import torch

@pytest.fixture
def setup_data():
    # Normal input data
    completion_input_ids = torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8, 9], 
                                         [10, 11, 12, 13, 14, 15, 16, 17, 18]])
    left_pad_tokens_per_prompt = torch.tensor([3, 2])
    max_left_pad = 5
    pad_token_id = 0
    expected_mask = torch.tensor([[0, 0, 0, 1, 1, 1, 1, 1, 1],
                                  [0, 0, 1, 1, 1, 1, 1, 1, 1]])
    
    # Empty input data
    empty_completion_input_ids = torch.tensor([[], []])
    empty_left_pad_tokens_per_prompt = torch.tensor([0, 0])
    empty_expected_mask = torch.tensor([[], []])
    
    return {
        "normal": (completion_input_ids, left_pad_tokens_per_prompt, max_left_pad, pad_token_id, expected_mask),
        "empty": (empty_completion_input_ids, empty_left_pad_tokens_per_prompt, max_left_pad, pad_token_id, empty_expected_mask)
    }

def test_create_completion_attention_mask_normal(setup_data):
    completion_input_ids, left_pad_tokens_per_prompt, max_left_pad, pad_token_id, expected_mask = setup_data["normal"]
    result = create_completion_attention_mask(completion_input_ids, left_pad_tokens_per_prompt, max_left_pad, pad_token_id)
    assert torch.equal(result, expected_mask), f"Expected {expected_mask} but got {result}"

def test_create_completion_attention_mask_empty(setup_data):
    completion_input_ids, left_pad_tokens_per_prompt, max_left_pad, pad_token_id, expected_mask = setup_data["empty"]
    result = create_completion_attention_mask(completion_input_ids, left_pad_tokens_per_prompt, max_left_pad, pad_token_id)
    assert torch.equal(result, expected_mask), f"Expected {expected_mask} but got {result}"

def test_create_completion_attention_mask_invalid_inputs():
    with pytest.raises(ValueError):
        create_completion_attention_mask(None, None, None, None)
    with pytest.raises(ValueError):
        create_completion_attention_mask(torch.tensor([1, 2]), torch.tensor([1]), 5, 0)
    with pytest.raises(ValueError):
        create_completion_attention_mask(torch.tensor([[1, 2], [3, 4]]), torch.tensor([1]), 5, 0)

# Assuming there's no asynchronous behavior in this function, so no async tests needed.