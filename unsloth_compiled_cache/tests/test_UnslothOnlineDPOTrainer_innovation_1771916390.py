import pytest
from transformers import PreTrainedTokenizerBase

class MockTokenizer(PreTrainedTokenizerBase):
    def __init__(self, bos_token_id=None):
        self.bos_token_id = bos_token_id
        self.vocab_size = 1000
        self.special_tokens_map = {'bos_token': '<|startoftext|>'}

    def tokenize(self, text, add_special_tokens=False):
        return text.split()

    def convert_tokens_to_ids(self, tokens):
        return [ord(token[0]) % self.vocab_size for token in tokens]

    def __call__(self, text, add_special_tokens=None, **kwargs):
        if add_special_tokens is None:
            add_special_tokens = False
        if add_special_tokens and self.bos_token_id is not None:
            tokens = [self.bos_token] + text.split()
        else:
            tokens = text.split()
        return {
            "input_ids": self.convert_tokens_to_ids(tokens),
            "attention_mask": [1] * len(tokens)
        }

def test_tokenize_row_happy_path():
    tokenizer = MockTokenizer(bos_token_id=483)
    feature = {"prompt": "Hello world"}
    result = tokenize_row(feature, is_encoder_decoder=False, tokenizer=tokenizer)
    expected = {
        "prompt_input_ids": [483, 72, 101, 108, 108, 111],
        "prompt_attention_mask": [1, 1, 1, 1, 1, 1]
    }
    assert result == expected

def test_tokenize_row_encoder_decoder():
    tokenizer = MockTokenizer(bos_token_id=None)
    feature = {"prompt": "Hello world"}
    result = tokenize_row(feature, is_encoder_decoder=True, tokenizer=tokenizer)
    expected = {
        "prompt_input_ids": [483, 72, 101, 108, 108, 111],
        "prompt_attention_mask": [1, 1, 1, 1, 1, 1]
    }
    assert result == expected

def test_tokenize_row_empty_prompt():
    tokenizer = MockTokenizer(bos_token_id=483)
    feature = {"prompt": ""}
    result = tokenize_row(feature, is_encoder_decoder=False, tokenizer=tokenizer)
    expected = {
        "prompt_input_ids": [483],
        "prompt_attention_mask": [1]
    }
    assert result == expected

def test_tokenize_row_none_prompt():
    tokenizer = MockTokenizer(bos_token_id=483)
    feature = {"prompt": None}
    result = tokenize_row(feature, is_encoder_decoder=False, tokenizer=tokenizer)
    assert result is None

def test_tokenize_row_bos_token_already_present():
    tokenizer = MockTokenizer(bos_token_id=None)
    feature = {"prompt": "<|startoftext|>Hello world"}
    result = tokenize_row(feature, is_encoder_decoder=False, tokenizer=tokenizer)
    expected = {
        "prompt_input_ids": [72, 101, 108, 108, 111],
        "prompt_attention_mask": [1, 1, 1, 1, 1]
    }
    assert result == expected

def test_tokenize_row_invalid_feature_type():
    tokenizer = MockTokenizer(bos_token_id=483)
    feature = {"prompt": 123}
    result = tokenize_row(feature, is_encoder_decoder=False, tokenizer=tokenizer)
    assert result is None