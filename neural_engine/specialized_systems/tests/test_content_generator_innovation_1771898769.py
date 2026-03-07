import pytest

from neural_engine.specialized_systems.content_generator import ContentGenerator

@pytest.fixture
def content_generator():
    return ContentGenerator()

def test_happy_path(content_generator):
    result = content_generator.generate_haiku("nature")
    assert isinstance(result, str)
    assert "Code flows like water," in result
    assert "nature" in result
    assert "Silence brings the bug." in result

def test_edge_case_empty_topic(content_generator):
    result = content_generator.generate_haiku("")
    assert isinstance(result, str)
    assert "Code flows like water," in result
    assert "" not in result
    assert "Silence brings the bug." in result

def test_edge_case_none_topic(content_generator):
    result = content_generator.generate_haiku(None)
    assert isinstance(result, str)
    assert "Code flows like water," in result
    assert None not in result
    assert "Silence brings the bug." in result

def test_error_case_invalid_input_type(content_generator):
    with pytest.raises(TypeError) as exc_info:
        content_generator.generate_haiku(123)
    assert str(exc_info.value) == "generate_haiku() argument 'topic' must be a string"