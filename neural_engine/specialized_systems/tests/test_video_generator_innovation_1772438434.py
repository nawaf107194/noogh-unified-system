import pytest

from neural_engine.specialized_systems.video_generator import get_video_generator, VideoGenerator

@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    global _video_generator
    _video_generator = None

def test_get_video_generator_happy_path():
    """Test the happy path of the function."""
    video_gen1 = get_video_generator()
    video_gen2 = get_video_generator()
    
    assert video_gen1 is not None
    assert isinstance(video_gen1, VideoGenerator)
    assert video_gen1 is video_gen2

def test_get_video_generator_no_global_instance():
    """Test when no global instance exists."""
    global _video_generator
    _video_generator = None
    
    video_gen = get_video_generator()
    
    assert video_gen is not None
    assert isinstance(video_gen, VideoGenerator)

def test_get_video_generator_with_existing_instance():
    """Test when a global instance already exists."""
    existing_instance = VideoGenerator()
    global _video_generator
    _video_generator = existing_instance
    
    video_gen = get_video_generator()
    
    assert video_gen is not None
    assert isinstance(video_gen, VideoGenerator)
    assert video_gen is existing_instance

def test_get_video_generator_async_behavior(mocker):
    """Test the async behavior of the function."""
    mock_video_gen = mocker.patch('neural_engine.specialized_systems.video_generator.VideoGenerator')
    
    video_gen1 = get_video_generator()
    video_gen2 = get_video_generator()
    
    assert mock_video_gen.call_count == 1
    assert video_gen1 is not None
    assert isinstance(video_gen1, VideoGenerator)
    assert video_gen1 is video_gen2