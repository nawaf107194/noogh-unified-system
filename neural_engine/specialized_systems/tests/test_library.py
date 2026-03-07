import pytest
from typing import List
from unittest.mock import MagicMock
from neural_engine.specialized_systems.library import PromptTemplate

class MockLibrary:
    def __init__(self):
        self.prompts = {
            'prompt1': PromptTemplate(id='prompt1', usage_count=5),
            'prompt2': PromptTemplate(id='prompt2', usage_count=10),
            'prompt3': PromptTemplate(id='prompt3', usage_count=15),
            'prompt4': PromptTemplate(id='prompt4', usage_count=20),
            'prompt5': PromptTemplate(id='prompt5', usage_count=25),
            'prompt6': PromptTemplate(id='prompt6', usage_count=30),
            'prompt7': PromptTemplate(id='prompt7', usage_count=35),
            'prompt8': PromptTemplate(id='prompt8', usage_count=40),
            'prompt9': PromptTemplate(id='prompt9', usage_count=45),
            'prompt10': PromptTemplate(id='prompt10', usage_count=50),
            'prompt11': PromptTemplate(id='prompt11', usage_count=55),
            'prompt12': PromptTemplate(id='prompt12', usage_count=60),
        }

@pytest.fixture
def library():
    return MockLibrary()

def test_get_popular_happy_path(library):
    popular_prompts = library.get_popular()
    assert len(popular_prompts) == 10
    assert popular_prompts[0].id == 'prompt12'
    assert popular_prompts[-1].id == 'prompt3'

def test_get_popular_with_custom_limit(library):
    popular_prompts = library.get_popular(5)
    assert len(popular_prompts) == 5
    assert popular_prompts[0].id == 'prompt12'
    assert popular_prompts[-1].id == 'prompt8'

def test_get_popular_empty_list(library):
    library.prompts = {}
    popular_prompts = library.get_popular()
    assert len(popular_prompts) == 0

def test_get_popular_none_input(library):
    with pytest.raises(TypeError):
        library.get_popular(None)

def test_get_popular_invalid_limit_type(library):
    with pytest.raises(TypeError):
        library.get_popular('ten')

def test_get_popular_limit_zero(library):
    popular_prompts = library.get_popular(0)
    assert len(popular_prompts) == 0

def test_get_popular_limit_negative(library):
    with pytest.raises(ValueError):
        library.get_popular(-1)

def test_get_popular_limit_exceeding_items(library):
    popular_prompts = library.get_popular(20)
    assert len(popular_prompts) == 12  # Assuming there are 12 items in the mock library

# Since the function does not have any async behavior, we skip testing for async behavior.