import pytest
import torch

def chunked_selective_log_softmax(logits, index):
    # Split into 4 chunks only
    chunked_logits = torch.chunk(logits.reshape(-1, logits.shape[-1]), chunks=4, dim=0)
    chunked_index = torch.chunk(index.reshape(-1), chunks=4, dim=0)
    all_per_token_logps = []
    for chunk_logits, chunk_index in zip(chunked_logits, chunked_index):
        chunk_logits = chunk_logits.to(torch.float32)
        selected_logits = torch.gather(chunk_logits, dim=-1, index=chunk_index.unsqueeze(-1)).squeeze(-1)
        logsumexp_values = torch.logsumexp(chunk_logits, dim=-1)
        per_token_logps = selected_logits - logsumexp_values
        all_per_token_logps.append(per_token_logps)
    all_per_token_logps = torch.concat(all_per_token_logps)
    all_per_token_logps = all_per_token_logps.reshape((logits.shape[0], logits.shape[1]))
    return all_per_token_logps

@pytest.mark.parametrize("logits, index, expected", [
    (torch.tensor([[2.0, 1.0]]), torch.tensor([0]), torch.tensor([[0.69314718, -1.74110112]])),
    (torch.tensor([[1.0, 2.0], [1.5, 0.5]]), torch.tensor([0, 1]), torch.tensor([[0.69314718, 0.69314718]])),
])
def test_chunked_selective_log_softmax_happy_path(logits, index, expected):
    result = chunked_selective_log_softmax(logits, index)
    assert torch.allclose(result, expected, atol=1e-5)

@pytest.mark.parametrize("logits, index", [
    (None, torch.tensor([0])),
    (torch.tensor([[2.0, 1.0]]), None),
    (torch.tensor([]), torch.tensor([0])),
    (torch.tensor([[2.0, 1.0]]), torch.tensor([2])),
])
def test_chunked_selective_log_softmax_edge_cases(logits, index):
    result = chunked_selective_log_softmax(logits, index)
    assert result is None

@pytest.mark.parametrize("logits, index", [
    (torch.tensor([[2.0, 1.0]]), torch.tensor([-1])),
    (torch.tensor([[-1.0, 1.0], [1.5, 0.5]]), torch.tensor([0, 2])),
])
def test_chunked_selective_log_softmax_error_cases(logits, index):
    result = chunked_selective_log_softmax(logits, index)
    assert result is None