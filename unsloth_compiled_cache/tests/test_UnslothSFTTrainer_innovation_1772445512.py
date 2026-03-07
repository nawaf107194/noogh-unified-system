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
    all_per_token_logps = torch.cat(all_per_token_logps)
    all_per_token_logps = all_per_token_logps.reshape((logits.shape[0], logits.shape[1]))
    return all_per_token_logps

@pytest.mark.parametrize("logits, index, expected", [
    (
        torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
        torch.tensor([1, 2]),
        torch.tensor([-1.7918, -0.6931])
    ),
    (
        torch.tensor([[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]),
        torch.tensor([2, 1]),
        torch.tensor([-0.6931, -1.7918])
    ),
    (
        torch.empty((0, 3)),
        torch.empty(0),
        torch.empty(0)
    ),
    (
        None,
        None,
        None
    )
])
def test_chunked_selective_log_softmax(logits, index, expected):
    result = chunked_selective_log_softmax(logits, index)
    
    assert torch.allclose(result, expected) if expected is not None else result is None

@pytest.mark.parametrize("logits, index", [
    (
        torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
        torch.tensor([2])
    ),
    (
        torch.tensor([]),
        torch.tensor([])
    )
])
def test_chunked_selective_log_softmax_error_cases(logits, index):
    with pytest.raises(RuntimeError):
        chunked_selective_log_softmax(logits, index)