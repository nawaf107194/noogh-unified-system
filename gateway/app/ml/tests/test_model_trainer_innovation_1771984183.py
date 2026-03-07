import pytest
from unittest.mock import patch
from transformers import AutoTokenizer, AutoModelForCausalLM, Dataset, TrainingArguments, Trainer
from src.gateway.app.ml.model_trainer import ModelTrainer

@pytest.fixture
def model_trainer():
    return ModelTrainer(model_name="gpt2", device="cpu")

def test_train_model_happy_path(model_trainer):
    data = [{"text": "Hello, world!"}]
    output_dir = "./test_output"
    
    result = model_trainer.train_model(data, output_dir)
    
    assert result["success"] is True
    assert result["training_loss"] is not None
    assert result["global_step"] > 0
    assert "metrics" in result

def test_train_model_empty_data(model_trainer):
    data = []
    output_dir = "./test_output"
    
    result = model_trainer.train_model(data, output_dir)
    
    assert result["success"] is False
    assert result["error"].startswith("Dataset must not be empty")

def test_train_model_none_data(model_trainer):
    data = None
    output_dir = "./test_output"
    
    result = model_trainer.train_model(data, output_dir)
    
    assert result["success"] is False
    assert result["error"].startswith("Data cannot be None")

def test_train_model_invalid_device(model_trainer):
    model_trainer.device = "invalid_device"
    data = [{"text": "Hello, world!"}]
    output_dir = "./test_output"
    
    with pytest.raises(NotImplementedError) as e:
        result = model_trainer.train_model(data, output_dir)
        
    assert str(e.value).startswith("Device 'invalid_device' is not supported")

def test_train_model_exception_during_training(model_trainer):
    data = [{"text": "Hello, world!"}]
    output_dir = "./test_output"
    
    with patch.object(AutoTokenizer, 'from_pretrained', side_effect=Exception("Simulated error")):
        result = model_trainer.train_model(data, output_dir)
        
    assert result["success"] is False
    assert result["error"].startswith("Training failed")