import pytest
from unittest.mock import patch, MagicMock
from src.gateway.app.ml.intelligent_training import _setup_model, TrainingConfig
from transformers import AutoTokenizer, AutoModelForCausalLM

@pytest.fixture
def mock_config():
    return TrainingConfig(model_name="test-model", use_gpu=False)

@patch('transformers.AutoTokenizer.from_pretrained')
@patch('transformers.AutoModelForCausalLM.from_pretrained')
def test_setup_model_happy_path(mock_model, mock_tokenizer, mock_config):
    # Setup
    mock_tokenizer.return_value = MagicMock()
    mock_model.return_value = MagicMock()

    # Call the function
    model, tokenizer = _setup_model(mock_config)

    # Assertions
    assert model == mock_model.return_value
    assert tokenizer == mock_tokenizer.return_value
    mock_tokenizer.assert_called_once_with("test-model")
    mock_model.assert_called_once_with(
        "test-model", torch_dtype=torch.float32
    )

@patch('transformers.AutoTokenizer.from_pretrained')
def test_setup_model_gpu(mock_tokenizer, mock_config):
    # Setup
    mock_config.use_gpu = True
    mock_tokenizer.return_value = MagicMock()
    mock_model.return_value = MagicMock()

    with patch('torch.cuda.is_available', return_value=True):
        # Call the function
        model, tokenizer = _setup_model(mock_config)

        # Assertions
        assert model == mock_model.return_value
        assert tokenizer == mock_tokenizer.return_value
        mock_tokenizer.assert_called_once_with("test-model")
        mock_model.assert_called_once_with(
            "test-model", torch_dtype=torch.float16
        )
        assert model.device.type == 'cuda'

@patch('transformers.AutoTokenizer.from_pretrained')
def test_setup_model_no_pad_token(mock_tokenizer, mock_config):
    # Setup
    mock_tokenizer.return_value = MagicMock(pad_token=None)
    mock_model.return_value = MagicMock()

    with patch('torch.cuda.is_available', return_value=True):
        # Call the function
        model, tokenizer = _setup_model(mock_config)

        # Assertions
        assert model == mock_model.return_value
        assert tokenizer == mock_tokenizer.return_value
        mock_tokenizer.assert_called_once_with("test-model")
        mock_model.assert_called_once_with(
            "test-model", torch_dtype=torch.float16
        )
        assert tokenizer.pad_token == tokenizer.eos_token

@patch('transformers.AutoTokenizer.from_pretrained')
def test_setup_model_empty_config(mock_tokenizer):
    # Setup
    with pytest.raises(ValueError) as exc_info:
        _setup_model(None)

    # Assertions
    assert "Invalid config" in str(exc_info.value)