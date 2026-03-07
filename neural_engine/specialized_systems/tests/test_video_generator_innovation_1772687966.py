import pytest
from neural_engine.specialized_systems.video_generator import VideoGenerator

def test_video_generator_init_happy_path():
    # Test with default model_id
    video_gen = VideoGenerator()
    assert video_gen.model_id == "stabilityai/stable-video-diffusion-img2vid-xt"
    assert video_gen.pipe is None
    assert video_gen.device == "cuda"
    assert video_gen._initialized is False

    # Test with custom model_id
    custom_model_id = "custom/model-id"
    video_gen = VideoGenerator(custom_model_id)
    assert video_gen.model_id == custom_model_id
    assert video_gen.pipe is None
    assert video_gen.device == "cuda"
    assert video_gen._initialized is False

def test_video_generator_init_edge_cases():
    # Test with empty string model_id
    video_gen = VideoGenerator("")
    assert video_gen.model_id == ""
    assert video_gen.pipe is None
    assert video_gen.device == "cuda"
    assert video_gen._initialized is False

    # Test with None model_id
    video_gen = VideoGenerator(None)
    assert video_gen.model_id is None
    assert video_gen.pipe is None
    assert video_gen.device == "cuda"
    assert video_gen._initialized is False

def test_video_generator_init_logging(caplog):
    model_id = "test-model-id"
    VideoGenerator(model_id)
    assert f"VideoGenerator initialized with model: {model_id}" in caplog.text