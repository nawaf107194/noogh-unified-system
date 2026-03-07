import pytest

from neural_engine.specialized_systems.content_generator import ContentGenerator

def test_generate_haiku_happy_path():
    generator = ContentGenerator()
    result = generator.generate_haiku("Nature")
    assert isinstance(result, str)
    assert "Code flows like water," in result
    assert "Nature is the stone inside," in result
    assert "Silence brings the bug." in result

def test_generate_haiku_empty_input():
    generator = ContentGenerator()
    result = generator.generate_haiku("")
    assert isinstance(result, str)
    assert "Code flows like water," in result
    assert " is the stone inside," in result  # Topic is empty, should still generate a valid haiku
    assert "Silence brings the bug." in result

def test_generate_haiku_none_input():
    generator = ContentGenerator()
    result = generator.generate_haiku(None)
    assert isinstance(result, str)
    assert "Code flows like water," in result
    assert " is the stone inside," in result  # Topic is None, should still generate a valid haiku
    assert "Silence brings the bug." in result

def test_generate_haiku_boundary_input():
    generator = ContentGenerator()
    result = generator.generate_haiku("A")
    assert isinstance(result, str)
    assert "Code flows like water," in result
    assert "A is the stone inside," in result  # Topic is a single character
    assert "Silence brings the bug." in result

def test_generate_haiku_invalid_input_type():
    generator = ContentGenerator()
    with pytest.raises(TypeError):
        generator.generate_haiku(123)

def test_generate_haiku_async_behavior():
    import asyncio
    
    async def check_result():
        generator = ContentGenerator()
        return await generator.generate_haiku("Async")
    
    result = asyncio.run(check_result())
    assert isinstance(result, str)
    assert "Code flows like water," in result
    assert "Async is the stone inside," in result  # Topic is a string
    assert "Silence brings the bug." in result