import pytest

from neural_engine.tools.media_tools import get_media_status

def mock_get_generator(generator_type):
    class MockGenerator:
        def get_status(self):
            return {"status": f"{generator_type}_ok"}
    return MockGenerator

@pytest.fixture
def image_generator_mock():
    return mock_get_generator("image")

@pytest.fixture
def audio_generator_mock():
    return mock_get_generator("audio")

@pytest.fixture
def video_generator_mock():
    return mock_get_generator("video")

def test_happy_path(image_generator_mock, audio_generator_mock, video_generator_mock):
    # Mock the import behavior
    from neural_engine.specialized_systems.image_generator import get_image_generator
    from neural_engine.specialized_systems.audio_generator import get_audio_generator
    from neural_engine.specialized_systems.video_generator import get_video_generator
    
    get_image_generator.return_value = image_generator_mock
    get_audio_generator.return_value = audio_generator_mock
    get_video_generator.return_value = video_generator_mock
    
    status = get_media_status()
    
    assert status == {
        "image_generator": {"status": "image_ok"},
        "audio_generator": {"status": "audio_ok"},
        "video_generator": {"status": "video_ok"},
        "summary_ar": "حالة الوسائط: صور ✅، صوت ✅، فيديو ✅"
    }

def test_error_handling():
    # Mock the import behavior with exceptions
    from neural_engine.specialized_systems.image_generator import get_image_generator
    
    def mock_get_image_generator():
        raise ImportError("Failed to import image generator")
    
    get_image_generator.side_effect = mock_get_image_generator
    
    status = get_media_status()
    
    assert status == {
        "image_generator": {"status": "error", "error": "Failed to import image generator"},
        "audio_generator": {"status": "unknown"},
        "video_generator": {"status": "unknown"},
        "summary_ar": "حالة الوسائط: صور ✅، صوت ✅، فيديو ✅"
    }

def test_missing_generators():
    # Mock the import behavior with missing generators
    from neural_engine.specialized_systems.image_generator import get_image_generator
    from neural_engine.specialized_systems.audio_generator import get_audio_generator
    from neural_engine.specialized_systems.video_generator import get_video_generator
    
    get_image_generator.return_value = None
    get_audio_generator.return_value = None
    get_video_generator.return_value = None
    
    status = get_media_status()
    
    assert status == {
        "image_generator": {"status": "unknown"},
        "audio_generator": {"status": "unknown"},
        "video_generator": {"status": "unknown"},
        "summary_ar": "حالة الوسائط: صور ✅، صوت ✅، فيديو ✅"
    }