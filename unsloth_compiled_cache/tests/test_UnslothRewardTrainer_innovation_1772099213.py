import pytest
import torch

def align_logprobs_with_mask(
    logprob_tensor: torch.Tensor,
    attention_mask: torch.Tensor,
    pad_value: float = 0.0
) -> torch.Tensor:
    """
    Aligns a log probability tensor with a given attention mask.
    """

    device = logprob_tensor.device
    batch_size, logprob_seq_len = logprob_tensor.shape
    mask_seq_len = attention_mask.shape[1]

    padded_logprobs = torch.full(
        attention_mask.shape,
        fill_value=pad_value,
        dtype=logprob_tensor.dtype,
        device=device
    )

    left_pad_counts = torch.argmax(attention_mask, dim=1)

    cols = torch.arange(logprob_seq_len, device=device)
    dest_indices = left_pad_counts.unsqueeze(1) + cols

    # Create destination row indices
    # Shape: [batch_size, logprob_seq_len]
    row_indices = torch.arange(batch_size, device=device).unsqueeze(1).expand_as(dest_indices)

    # --- 4. Filter out-of-bounds indices and perform assignment ---
    # Create a mask to identify only the indices that are within the bounds
    # of the target tensor's sequence length.
    valid_mask = dest_indices < mask_seq_len

    # Use this mask to select only the valid row indices, column indices,
    # and the corresponding values from the logprob tensor.
    # This flattens the selected elements into 1D tensors.
    valid_rows = row_indices[valid_mask]
    valid_cols = dest_indices[valid_mask]
    valid_vals = logprob_tensor[valid_mask]

    # Place the valid values into their correct positions in the padded tensor
    # using a single, efficient advanced indexing operation.
    padded_logprobs[valid_rows, valid_cols] = valid_vals

    return padded_logprobs

# Tests

def test_align_logprobs_with_mask_happy_path():
    logprob_tensor = torch.tensor(
        [[-1.0, -2.0, 0.0],
         [-3.0, 0.0, 1.0]],
        dtype=torch.float32
    )
    attention_mask = torch.tensor(
        [[1, 1, 1],
         [1, 0, 1]],
        dtype=torch.long
    )
    expected_output = torch.tensor(
        [[-1.0, -2.0, 0.0],
         [-3.0, 0.0, 1.0]],
        dtype=torch.float32
    )
    output = align_logprobs_with_mask(logprob_tensor, attention_mask)
    assert torch.equal(output, expected_output)

def test_align_logprobs_with_mask_empty():
    logprob_tensor = torch.empty((0, 0), dtype=torch.float32)
    attention_mask = torch.empty((0, 0), dtype=torch.long)
    expected_output = torch.empty((0, 0), dtype=torch.float32)
    output = align_logprobs_with_mask(logprob_tensor, attention_mask)
    assert torch.equal(output, expected_output)

def test_align_logprobs_with_mask_none():
    logprob_tensor = None
    attention_mask = None
    with pytest.raises(TypeError):
        align_logprobs_with_mask(logprob_tensor, attention_mask)

def test_align_logprobs_with_mask_invalid_input_shape():
    logprob_tensor = torch.tensor(
        [[-1.0, -2.0, 0.0]],
        dtype=torch.float32
    )
    attention_mask = torch.tensor(
        [[1, 1],
         [1, 0]],
        dtype=torch.long
    )
    with pytest.raises(ValueError):
        align_logprobs_with_mask(logprob_tensor, attention_mask)

def test_align_logprobs_with_mask_invalid_pad_value():
    logprob_tensor = torch.tensor(
        [[-1.0, -2.0, 0.0],
         [-3.0, 0.0, 1.0]],
        dtype=torch.float32
    )
    attention_mask = torch.tensor(
        [[1, 1, 1],
         [1, 0, 1]],
        dtype=torch.long
    )
    with pytest.raises(TypeError):
        align_logprobs_with_mask(logprob_tensor, attention_mask, pad_value='invalid')