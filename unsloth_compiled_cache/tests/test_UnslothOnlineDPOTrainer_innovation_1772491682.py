import pytest
import torch

def chunked_selective_log_softmax(logits, index):
    # Split into 4 chunks only
    chunked_logits = torch.chunk(logits.reshape(-1, logits.shape[-1]), chunks=4, dim=0)
    chunked_index = torch.chunk(index.reshape(-1), chunks=4, dim=0)
    all_per_token_logps = []
    # Below loop does the same as selective_log_softmax(chunk_logits, chunk_index)
    for chunk_logits, chunk_index in zip(chunked_logits, chunked_index):
        chunk_logits = chunk_logits.to(torch.float32)
        selected_logits = torch.gather(chunk_logits, dim=-1, index=chunk_index.unsqueeze(-1)).squeeze(-1)
        logsumexp_values = torch.logsumexp(chunk_logits, dim=-1)
        per_token_logps = selected_logits - logsumexp_values
        all_per_token_logps.append(per_token_logps)
    pass
    all_per_token_logps = torch.cat(all_per_token_logps)
    all_per_token_logps = all_per_token_logps.reshape((logits.shape[0], logits.shape[1]))
    return all_per_token_logps

def test_chunked_selective_log_softmax_happy_path():
    # Happy path with normal inputs
    logits = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    index = torch.tensor([[0], [1]])
    expected_output = torch.tensor([
        [1.0 - torch.logsumexp(logits[0], dim=0)],
        [5.0 - torch.logsumexp(logits[1], dim=0)]
    ])
    assert torch.allclose(chunked_selective_log_softmax(logits, index), expected_output)

def test_chunked_selective_log_softmax_empty_input():
    # Edge case with empty input
    logits = torch.tensor([])
    index = torch.tensor([])
    expected_output = torch.tensor([])
    assert torch.allclose(chunked_selective_log_softmax(logits, index), expected_output)

def test_chunked_selective_log_softmax_none_input():
    # Edge case with None input
    logits = None
    index = None
    expected_output = None
    assert chunked_selective_log_softmax(logits, index) is expected_output

def test_chunked_selective_log_softmax_boundary_case():
    # Boundary case with boundary values
    logits = torch.tensor([[1.0e-6, 2.0e-6]])
    index = torch.tensor([[0]])
    expected_output = torch.tensor([
        [1.0e-6 - torch.logsumexp(logits[0], dim=0)]
    ])
    assert torch.allclose(chunked_selective_log_softmax(logits, index), expected_output)

def test_chunked_selective_log_softmax_invalid_input():
    # Error case with invalid input
    logits = torch.tensor([[1.0, 2.0, 3.0]])
    index = torch.tensor([[1]])  # Index out of bounds
    expected_output = None
    assert chunked_selective_log_softmax(logits, index) is expected_output