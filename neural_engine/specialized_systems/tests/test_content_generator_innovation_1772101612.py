import pytest

from neural_engine.specialized_systems.content_generator import ContentGenerator

@pytest.fixture
def content_generator():
    return ContentGenerator()

def test_generate_haiku_happy_path(content_generator):
    topic = "Mountain"
    expected_output = "Code flows like water,\nMountain is the stone inside,\nSilence brings the bug."
    assert content_generator.generate_haiku(topic) == expected_output

def test_generate_haiku_empty_input(content_generator):
    topic = ""
    expected_output = "Code flows like water,\n is the stone inside,\nSilence brings the bug."
    assert content_generator.generate_haiku(topic) == expected_output

def test_generate_haiku_none_input(content_generator):
    topic = None
    expected_output = "Code flows like water,\n is the stone inside,\nSilence brings the bug."
    assert content_generator.generate_haiku(topic) == expected_output

def test_generate_haiku_boundary_input_max_length(content_generator):
    topic = "A" * 100
    expected_output = "Code flows like water,\nA" * 49 + " is the stone inside,\nSilence brings the bug."
    assert content_generator.generate_haiku(topic) == expected_output

def test_generate_haiku_boundary_input_min_length(content_generator):
    topic = "a"
    expected_output = "Code flows like water,\na is the stone inside,\nSilence brings the bug."
    assert content_generator.generate_haiku(topic) == expected_output