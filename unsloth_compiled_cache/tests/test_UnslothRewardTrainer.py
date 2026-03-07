import pytest
import torch
from UnslothRewardTrainer import chunked_selective_log_softmax

def test_happy_path():
    logits = torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
    index = torch.tensor([0, 1, 0, 1])
    expected_output = torch.tensor([-1.5578, -2.5578, -5.5578, -6.5578])
    output = chunked_selective_log_softmax(logits, index)
    assert torch.allclose(output, expected_output, atol=1e-4)

def test_empty_inputs():
    logits = torch.tensor([])
    index = torch.tensor([])
    with pytest.raises(IndexError):
        chunked_selective_log_softmax(logits, index)

def test_none_inputs():
    with pytest.raises(AttributeError):
        chunked_selective_log_softmax(None, None)

def test_boundary_inputs():
    logits = torch.tensor([[1.0], [2.0], [3.0], [4.0]])
    index = torch.tensor([0, 0, 0, 0])
    expected_output = torch.tensor([-1.5578, -2.5578, -3.5578, -4.5578])
    output = chunked_selective_log_softmax(logits, index)
    assert torch.allclose(output, expected_output, atol=1e-4)

def test_invalid_inputs():
    logits = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    index = torch.tensor([0, 1, 2])  # Invalid index
    with pytest.raises(IndexError):
        chunked_selective_log_softmax(logits, index)

def test_mismatched_shape_inputs():
    logits = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    index = torch.tensor([0, 1, 1])  # Mismatched shape
    with pytest.raises(RuntimeError):
        chunked_selective_log_softmax(logits, index)

# Note: The function does not have any async behavior, so no async tests are applicable.