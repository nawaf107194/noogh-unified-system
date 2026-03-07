import pytest
import torch
from unsloth_compiled_cache.UnslothNashMDTrainer import align_logprobs_with_mask

def test_align_logprobs_with_mask_happy_path():
    logprob_tensor = torch.tensor([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype=torch.float32)
    attention_mask = torch.tensor([[1, 1, 0], [1, 0, 0]], dtype=torch.float32)
    expected_output = torch.tensor([[0.1, 0.2, 0.0], [0.4, 0.0, 0.0]], dtype=torch.float32)

    output = align_logprobs_with_mask(logprob_tensor, attention_mask)
    assert torch.equal(output, expected_output)

def test_align_logprobs_with_mask_empty_inputs():
    logprob_tensor = torch.tensor([], dtype=torch.float32)
    attention_mask = torch.tensor([], dtype=torch.float32)
    expected_output = torch.tensor([], dtype=torch.float32)

    output = align_logprobs_with_mask(logprob_tensor, attention_mask)
    assert torch.equal(output, expected_output)

def test_align_logprobs_with_mask_none_inputs():
    logprob_tensor = None
    attention_mask = None
    expected_output = None

    output = align_logprobs_with_mask(logprob_tensor, attention_mask)
    assert output is expected_output

def test_align_logprobs_with_mask_boundary_conditions():
    # Test when all elements in the mask are zero (should return a tensor filled with pad value)
    logprob_tensor = torch.tensor([[0.1, 0.2], [0.3, 0.4]], dtype=torch.float32)
    attention_mask = torch.tensor([[0, 0], [0, 0]], dtype=torch.float32)
    expected_output = torch.tensor([[0.0, 0.0], [0.0, 0.0]], dtype=torch.float32)

    output = align_logprobs_with_mask(logprob_tensor, attention_mask)
    assert torch.equal(output, expected_output)

def test_align_logprobs_with_mask_invalid_inputs():
    logprob_tensor = torch.tensor([[0.1, 0.2], [0.3, 0.4]], dtype=torch.float32)
    attention_mask = torch.tensor([[], []], dtype=torch.float32)  # Invalid mask shape

    with pytest.raises(RuntimeError):
        output = align_logprobs_with_mask(logprob_tensor, attention_mask)