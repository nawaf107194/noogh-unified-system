import pytest
from unittest.mock import patch, mock_open

from neural_engine.model_authority import _load_openai_model

class LoadFailedError(Exception):
    pass

@patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
def test_load_openai_model_happy_path():
    from langchain_openai import ChatOpenAI
    model, tokenizer = _load_openai_model()
    assert isinstance(model, ChatOpenAI)
    assert isinstance(tokenizer, type(None))
    assert model.model == "gpt-3.5-turbo"
    assert model.api_key == "test_api_key"

@patch.dict('os.environ', {})
def test_load_openai_model_no_env_var():
    with pytest.raises(LoadFailedError) as exc_info:
        _load_openai_model()
    assert exc_info.value.args[1] == "OPENAI_API_KEY not set"

@patch.dict('os.environ', {'OPENAI_API_KEY': None})
def test_load_openai_model_none_api_key():
    with pytest.raises(LoadFailedError) as exc_info:
        _load_openai_model()
    assert exc_info.value.args[1] == "OPENAI_API_KEY not set"

def test_load_openai_model_import_failure(mocker):
    mocker.patch('langchain_openai.ChatOpenAI', side_effect=ImportError)
    with pytest.raises(LoadFailedError) as exc_info:
        _load_openai_model()
    assert exc_info.value.args[1] == "OpenAI load failed: ImportError('No module named \'langchain_openai\'')"

def test_load_openai_model_general_failure(mocker):
    mocker.patch('langchain_openai.ChatOpenAI', side_effect=Exception("Test failure"))
    with pytest.raises(LoadFailedError) as exc_info:
        _load_openai_model()
    assert exc_info.value.args[1] == "OpenAI load failed: Test failure"