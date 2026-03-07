import pytest
import torch

def test_chunked_hidden_states_selective_log_softmax_happy_path():
    hidden_states = torch.randn(10, 5)
    lm_head = torch.randn(5, 2)
    index = torch.tensor([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index)
    assert result.shape == (10,)

def test_chunked_hidden_states_selective_log_softmax_empty_index():
    hidden_states = torch.randn(5, 5)
    lm_head = torch.randn(5, 3)
    index = torch.tensor([])
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index)
    assert result.shape == (0,)

def test_chunked_hidden_states_selective_log_softmax_none_inputs():
    hidden_states = None
    lm_head = None
    index = None
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index)
    assert result is None

def test_chunked_hidden_states_selective_log_softmax_single_token():
    hidden_states = torch.randn(1, 5)
    lm_head = torch.randn(5, 1)
    index = torch.tensor([0])
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index)
    assert result.shape == (1,)

def test_chunked_hidden_states_selective_log_softmax_large_chunks():
    hidden_states = torch.randn(20, 5)
    lm_head = torch.randn(5, 3)
    index = torch.tensor([0, 1, 2, 3, 4] * 4)
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index, chunks=8)
    assert result.shape == (20,)

def test_chunked_hidden_states_selective_log_softmax_large_temperature():
    hidden_states = torch.randn(5, 5)
    lm_head = torch.randn(5, 3)
    index = torch.tensor([0, 1, 2, 3, 4])
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index, temperature=10.0)
    assert result.shape == (5,)

def test_chunked_hidden_states_selective_log_softmax_small_temperature():
    hidden_states = torch.randn(5, 5)
    lm_head = torch.randn(5, 3)
    index = torch.tensor([0, 1, 2, 3, 4])
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index, temperature=0.1)
    assert result.shape == (5,)

def test_chunked_hidden_states_selective_log_softmax_logit_scale_multiply():
    hidden_states = torch.randn(5, 5)
    lm_head = torch.randn(5, 3)
    index = torch.tensor([0, 1, 2, 3, 4])
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index, logit_scale_multiply=2.0)
    assert result.shape == (5,)

def test_chunked_hidden_states_selective_log_softmax_logit_scale_divide():
    hidden_states = torch.randn(5, 5)
    lm_head = torch.randn(5, 3)
    index = torch.tensor([0, 1, 2, 3, 4])
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index, logit_scale_divide=2.0)
    assert result.shape == (5,)

def test_chunked_hidden_states_selective_log_softmax_logit_softcapping():
    hidden_states = torch.randn(5, 5)
    lm_head = torch.randn(5, 3)
    index = torch.tensor([0, 1, 2, 3, 4])
    result = chunked_hidden_states_selective_log_softmax(hidden_states, lm_head, index, logit_softcapping=2.0)
    assert result.shape == (5,)