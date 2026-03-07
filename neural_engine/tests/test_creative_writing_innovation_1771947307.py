import pytest

from neural_engine.creative_writing import CreativeWritingEngine
from neural_engine.reasoning_engine import ReasoningEngine
from neural_engine.poetry_generator import PoetryGenerator
from neural_engine.story_teller import StoryTeller
import logging

# Mock logger for testing
class MockLogger:
    @staticmethod
    def info(message):
        pass

logger = MockLogger()

@pytest.fixture
def reasoning_engine():
    return ReasoningEngine()

@pytest.fixture
def poetry_generator(reasoning_engine):
    return PoetryGenerator(reasoning_engine)

@pytest.fixture
def story_teller(reasoning_engine):
    return StoryTeller(reasoning_engine)

def test_creative_writing_engine_happy_path(reasoning_engine, poetry_generator, story_teller):
    engine = CreativeWritingEngine(reasoning_engine)
    assert engine.poetry_generator == poetry_generator
    assert engine.story_teller == story_teller
    assert logger.info.call_args_list == [pytest.param("CreativeWritingEngine initialized", id="info_message")]

def test_creative_writing_engine_none_reasoning_engine():
    engine = CreativeWritingEngine(None)
    assert engine.poetry_generator is not None
    assert engine.story_teller is not None
    assert logger.info.call_args_list == [pytest.param("CreativeWritingEngine initialized", id="info_message")]

def test_creative_writing_engine_empty_reasoning_engine(reasoning_engine):
    reasoning_engine = None
    engine = CreativeWritingEngine(reasoning_engine)
    assert engine.poetry_generator is not None
    assert engine.story_teller is not None
    assert logger.info.call_args_list == [pytest.param("CreativeWritingEngine initialized", id="info_message")]

def test_creative_writing_engine_invalid_reasoning_engine():
    with pytest.raises(TypeError):
        CreativeWritingEngine(12345)