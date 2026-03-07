import pytest

from neural_engine.model_trainer import ModelTrainer

class MockModel:
    def generate(self, **kwargs):
        return torch.tensor([[100, 200, 300, 400]]), None

class MockTokenizer:
    def __init__(self):
        self.eos_token_id = 100

    def tokenizer(prompt, return_tensors="pt"):
        return {"input_ids": torch.tensor([[5, 6, 7]])}

    def decode(self, tokens, skip_special_tokens=True):
        return "response"

@pytest.fixture
def model_trainer():
    trainer = ModelTrainer()
    trainer.model = MockModel()
    trainer.tokenizer = MockTokenizer()
    return trainer

def test_generate_happy_path(model_trainer):
    result = model_trainer.generate("prompt", 256)
    assert result == "response"

def test_generate_empty_prompt(model_trainer):
    model_trainer.tokenizer.decode.return_value = "response"
    result = model_trainer.generate("", 256)
    assert result == "response"

def test_generate_none_prompt(model_trainer):
    result = model_trainer.generate(None, 256)
    assert result is None

def test_generate_max_new_tokens_boundary(model_trainer):
    model_trainer.tokenizer.decode.return_value = "response"
    result = model_trainer.generate("prompt", 1)
    assert result == "response"

def test_generate_invalid_model(model_trainer):
    model_trainer.model = None
    result = model_trainer.generate("prompt", 256)
    assert result is None

def test_generate_invalid_tokenizer(model_trainer):
    model_trainer.tokenizer = None
    result = model_trainer.generate("prompt", 256)
    assert result is None