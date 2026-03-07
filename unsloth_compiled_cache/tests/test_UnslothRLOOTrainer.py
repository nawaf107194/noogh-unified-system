import pytest

from unsloth_compiled_cache.UnslothRLOOTrainer import decode


def test_decode_happy_path():
    tokenizer = MockTokenizer()
    example = {"input_ids": [101, 202, 303, 404, 505]}
    expected_output = "Hello World"
    tokenizer.decode.return_value = expected_output
    result = decode(example, tokenizer)
    assert result == {"prompt": expected_output}


def test_decode_empty_input_ids():
    tokenizer = MockTokenizer()
    example = {"input_ids": []}
    expected_output = ""
    tokenizer.decode.return_value = expected_output
    result = decode(example, tokenizer)
    assert result == {"prompt": expected_output}


def test_decode_none_input_ids():
    tokenizer = MockTokenizer()
    example = {"input_ids": None}
    expected_output = None
    tokenizer.decode.return_value = expected_output
    result = decode(example, tokenizer)
    assert result == {"prompt": expected_output}


def test_decode_boundary_input_ids():
    tokenizer = MockTokenizer()
    example = {"input_ids": [0]}
    expected_output = ""
    tokenizer.decode.return_value = expected_output
    result = decode(example, tokenizer)
    assert result == {"prompt": expected_output}


class MockTokenizer:
    def __init__(self):
        self.decode = MagicMock()