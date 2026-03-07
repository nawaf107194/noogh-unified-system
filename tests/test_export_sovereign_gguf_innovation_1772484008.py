import pytest
from unittest.mock import patch, MagicMock

# Assuming FastLanguageModel and LORA_PATH are imported correctly
from export_sovereign_gguf import main, FastLanguageModel, LORA_PATH, GGUF_DIR

@pytest.fixture
def mock_model():
    return MagicMock()

@pytest.fixture
def mock_tokenizer():
    return MagicMock()

@pytest.fixture
def mock_save_pretrained_gguf():
    with patch.object(FastLanguageModel, 'save_pretrained_gguf', autospec=True) as mp:
        yield mp

@pytest.fixture
def mock_save_pretrained_merged():
    with patch.object(FastLanguageModel, 'save_pretrained_merged', autospec=True) as mp:
        yield mp

def test_main_happy_path(mock_model, mock_tokenizer, mock_save_pretrained_gguf):
    # Arrange
    mock_fast_language_model = FastLanguageModel.from_pretrained.return_value
    
    with patch('export_sovereign_gguf.FastLanguageModel', return_value=mock_fast_language_model) as MockFastLanguageModel:
        main()

    # Assert
    MockFastLanguageModel.assert_called_once_with(
        model_name=str(LORA_PATH),
        max_seq_length=1024,
        dtype=None,
        load_in_4bit=True,
    )
    
    mock_save_pretrained_gguf.assert_called_once_with(
        str(GGUF_DIR),
        mock_tokenizer,
        quantization_method="q8_0",
    )

def test_main_export_fails_no_exception(mock_model, mock_tokenizer, mock_save_pretrained_gguf):
    # Arrange
    mock_fast_language_model = FastLanguageModel.from_pretrained.return_value
    mock_save_pretrained_gguf.side_effect = Exception("Mock exception")
    
    with patch('export_sovereign_gguf.FastLanguageModel', return_value=mock_fast_language_model) as MockFastLanguageModel:
        main()

    # Assert
    MockFastLanguageModel.assert_called_once_with(
        model_name=str(LORA_PATH),
        max_seq_length=1024,
        dtype=None,
        load_in_4bit=True,
    )
    
    mock_save_pretrained_gguf.assert_called_once_with(
        str(GGUF_DIR),
        mock_tokenizer,
        quantization_method="q8_0",
    )

def test_main_export_fails_saves_as_16bit(mock_model, mock_tokenizer, mock_save_pretrained_gguf, mock_save_pretrained_merged):
    # Arrange
    mock_fast_language_model = FastLanguageModel.from_pretrained.return_value
    mock_save_pretrained_gguf.side_effect = Exception("Mock exception")
    
    with patch('export_sovereign_gguf.FastLanguageModel', return_value=mock_fast_language_model) as MockFastLanguageModel:
        main()

    # Assert
    MockFastLanguageModel.assert_called_once_with(
        model_name=str(LORA_PATH),
        max_seq_length=1024,
        dtype=None,
        load_in_4bit=True,
    )
    
    mock_save_pretrained_gguf.assert_called_once_with(
        str(GGUF_DIR),
        mock_tokenizer,
        quantization_method="q8_0",
    )

    mock_save_pretrained_merged.assert_called_once_with(
        str(GGUF_DIR / "hf_16bit"),
        mock_tokenizer,
        save_method="merged_16bit"
    )