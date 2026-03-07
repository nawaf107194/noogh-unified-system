import pytest
import torch

@pytest.fixture
def setup_tensors():
    logprob_tensor = torch.tensor([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    attention_mask = torch.tensor([[1, 1, 0], [1, 1, 1]])
    return logprob_tensor, attention_mask

def test_align_logprobs_with_mask_happy_path(setup_tensors):
    logprob_tensor, attention_mask = setup_tensors
    result = align_logprobs_with_mask(logprob_tensor, attention_mask)
    expected_result = torch.tensor([[0.1, 0.2, 0.0], [0.4, 0.5, 0.6]])
    assert torch.equal(result, expected_result)

def test_align_logprobs_with_mask_empty_input():
    logprob_tensor = torch.empty((0, 0))
    attention_mask = torch.empty((0, 0))
    result = align_logprobs_with_mask(logprob_tensor, attention_mask)
    expected_result = torch.empty((0, 0))
    assert torch.equal(result, expected_result)

def test_align_logprobs_with_mask_none_input():
    with pytest.raises(AttributeError):
        align_logprobs_with_mask(None, None)

def test_align_logprobs_with_mask_invalid_input():
    logprob_tensor = torch.tensor([1, 2, 3])
    attention_mask = torch.tensor([1, 0])
    with pytest.raises(AssertionError):
        align_logprobs_with_mask(logprob_tensor, attention_mask)

def test_align_logprobs_with_mask_boundary_case():
    logprob_tensor = torch.tensor([[0.1], [0.2]])
    attention_mask = torch.tensor([[1], [0]])
    result = align_logprobs_with_mask(logprob_tensor, attention_mask)
    expected_result = torch.tensor([[0.1], [0.0]])
    assert torch.equal(result, expected_result)

def test_align_logprobs_with_mask_different_device():
    logprob_tensor = torch.tensor([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]).cuda()
    attention_mask = torch.tensor([[1, 1, 0], [1, 1, 1]]).cuda()
    result = align_logprobs_with_mask(logprob_tensor, attention_mask)
    expected_result = torch.tensor([[0.1, 0.2, 0.0], [0.4, 0.5, 0.6]]).cuda()
    assert torch.equal(result, expected_result)

def test_align_logprobs_with_mask_pad_value():
    logprob_tensor = torch.tensor([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    attention_mask = torch.tensor([[1, 1, 0], [1, 1, 1]])
    result = align_logprobs_with_mask(logprob_tensor, attention_mask, pad_value=-1.0)
    expected_result = torch.tensor([[0.1, 0.2, -1.0], [0.4, 0.5, 0.6]])
    assert torch.equal(result, expected_result)