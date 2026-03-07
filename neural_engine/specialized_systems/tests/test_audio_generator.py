import pytest

from neural_engine.specialized_systems.audio_generator import AudioGenerator

def test_audio_generator_happy_path():
    """Test the AudioGenerator with normal inputs."""
    ag = AudioGenerator(model_type="bark")
    assert ag.model_type == "bark"
    assert ag.model is None
    assert ag.processor is None
    assert ag.device == "cuda"
    assert not ag._initialized
    assert logger.info.call_args_list == [call("AudioGenerator initialized with model type: bark")]

def test_audio_generator_edge_case_empty_model_type():
    """Test the AudioGenerator with an empty string for model_type."""
    ag = AudioGenerator(model_type="")
    assert ag.model_type == ""
    assert ag.model is None
    assert ag.processor is None
    assert ag.device == "cuda"
    assert not ag._initialized
    assert logger.info.call_args_list == [call("AudioGenerator initialized with model type: ")]

def test_audio_generator_edge_case_none_model_type():
    """Test the AudioGenerator with None for model_type."""
    ag = AudioGenerator(model_type=None)
    assert ag.model_type is None
    assert ag.model is None
    assert ag.processor is None
    assert ag.device == "cuda"
    assert not ag._initialized
    assert logger.info.call_args_list == [call("AudioGenerator initialized with model type: None")]

def test_audio_generator_error_case_invalid_model_type():
    """Test the AudioGenerator with an invalid model_type."""
    with pytest.raises(ValueError) as e:
        AudioGenerator(model_type="invalid")
    assert str(e.value) == "Invalid model_type. Supported types are 'bark' and 'coqui'."